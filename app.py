'''
Scrape metrics from target services and push them to PushGateway
'''
import docker
import logging
import os
import requests
import time

from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.exposition import basic_auth_handler
from prometheus_client import CollectorRegistry, push_to_gateway
from urllib.parse import urljoin

logging.basicConfig(level='INFO')

docker_client = docker.DockerClient(base_url='unix://tmp/docker.sock')

WORKING_DIR_LABEL = 'com.docker.compose.project.working_dir'
SCRAPE_LABEL = 'com.github.nmix.gate-up.scrape'

PUSHGATEWAY_URL = os.environ.get('PUSHGATEWAY_URL', 'http://pushgateway:9091')
PUSHGATEWAY_BASIC_AUTH_USERNAME = os.environ.get(
        'PUSHGATEWAY_BASIC_AUTH_USERNAME', '')
PUSHGATEWAY_BASIC_AUTH_PASSWORD = os.environ.get(
        'PUSHGATEWAY_BASIC_AUTH_PASSWORD', '')

SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', 5))
if SCRAPE_INTERVAL < 1:
    SCRAPE_INTERVAL = 1


def log(msg):
    logging.info(msg)


def project_containers():
    '''
    return list of compose project containers
    '''
    # --- get current container
    hostname = open('/etc/hostname').readline()[:-1]
    try:
        app_container = docker_client.containers.get(hostname)
    except docker.errors.NotFound:
        raise RuntimeError('Not in docker?')
    # --- filter project containers by working project
    working_dir = app_container.labels[WORKING_DIR_LABEL]
    labels = [f'{WORKING_DIR_LABEL}={working_dir}', SCRAPE_LABEL]
    containers = docker_client.containers.list(filters={'label': labels})
    containers = [c for c in containers if c != app_container]
    return containers


def get_container_scrape_params(container):
    '''
    return service port and path for scrape
    source Env = ['ENV_NAME1=VAL1', 'ENV_NAME2=VAL2', ...]
    '''
    envd = dict([e.split('=') for e in container.attrs['Config']['Env']])
    port = envd.get('SCRAPE_PORT', 80)
    path = envd.get('SCRAPE_PATH', '/metrics')
    return port, path


class collector:
    '''
    Pseudo-collector class

    To pushing metrics needs CollectorRegistry instance which works
    only with 'collector' instances: Counter, Gauge, etc

    Response from text_string_to_metric_families method is not the
    collectror, it just generator of Metric instances.

    @see https://clck.ru/h3aEm
    '''
    def __init__(self, url):
        self.url = url

    def collect(self):
        response = requests.get(self.url)
        return list(text_string_to_metric_families(response.text))


def push_gateway_handler(url, method, timeout, headers, data):
    '''
    handler for passing basic auth parameters
    '''
    return basic_auth_handler(
            url,
            method,
            timeout,
            headers,
            data,
            PUSHGATEWAY_BASIC_AUTH_USERNAME,
            PUSHGATEWAY_BASIC_AUTH_PASSWORD)


while True:
    time.sleep(SCRAPE_INTERVAL)
    for container in project_containers():
        # --- specify the metrics url
        port, path = get_container_scrape_params(container)
        url = urljoin(f'http://{container.name}:{port}', path)
        log(f'scrape metrics from {url}')
        # ---
        registry = CollectorRegistry()
        registry.register(collector(url))
        # --- push metrics to pushgateway
        push_to_gateway(
                PUSHGATEWAY_URL,
                job=container.name,
                registry=registry,
                handler=push_gateway_handler)
