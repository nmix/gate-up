'''
Scrape metrics from target services and push them to PushGateway
'''
import docker
import logging
import os
import requests
import time
import dataclasses
from urllib import parse

from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.exposition import basic_auth_handler
from prometheus_client import CollectorRegistry, push_to_gateway

import glom

# --- default values
DEFAULT_SCRAPE_PORT = 80
DEFAULT_SCRAPE_PATH = '/metrics'

# --- environment config
DOCKER_BASE_URL = os.environ.get('DOCKER_BASE_URL', 'unix://tmp/docker.sock')
SWARM_MODE = True if os.environ.get('SWARM_MODE') else False
JOB_PREFIX = os.environ.get('JOB_PREFIX', 'env')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
PUSHGATEWAY_URL = os.environ.get('PUSHGATEWAY_URL', 'http://pushgateway:9091')
PUSHGATEWAY_BASIC_AUTH_USERNAME = os.environ.get(
        'PUSHGATEWAY_BASIC_AUTH_USERNAME', '')
PUSHGATEWAY_BASIC_AUTH_PASSWORD = os.environ.get(
        'PUSHGATEWAY_BASIC_AUTH_PASSWORD', '')
SCRAPE_LABEL = os.environ.get('SCRAPE_LABEL', 'com.github.nmix.gate-up.scrape')
# --- @TODO: refactor required
SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', 5))
if SCRAPE_INTERVAL < 1:
    SCRAPE_INTERVAL = 1


logging.basicConfig(level=LOG_LEVEL)
logging.info('Gate UP!')


@dataclasses.dataclass
class Service():
    '''Service with metrics, e.g. docker container or swarm task

    Note:
    Do not confuse this class with swarm services

    Attributes:
    name - dns name (container or task name)
    labels - labels dict, e.g.
        {
            'com.docker.stack.namespace': 'gateup',
            'com.github.nmix.gate-up.scrape': ''
            }
    env - environment variables list, e.g. ['SCRAPE_PORT=9100']
    '''
    name: str
    labels: dict = dataclasses.field(default_factory=dict)
    env: list[int] = dataclasses.field(default_factory=list)

    @property
    def url(self) -> str:
        '''Service url for scrape metrics'''
        envd = dict([e.split('=') for e in self.env])
        port = envd.get('SCRAPE_PORT', DEFAULT_SCRAPE_PORT)
        path = envd.get('SCRAPE_PATH', DEFAULT_SCRAPE_PATH)
        return parse.urljoin(f'http://{self.name}:{port}', path)


def host_services() -> list[Service]:
    '''return containers services on host'''
    docker_client = docker.DockerClient(base_url=DOCKER_BASE_URL)
    services = []
    for container in docker_client.containers.list():
        name = container.name
        labels = glom.glom(container.attrs, 'Config.Labels')
        env = glom.glom(container.attrs, 'Config.Env')
        services.append(Service(name=name, labels=labels, env=env))
    return services


def swarm_task_services() -> list[Service]:
    '''return task services in swarm stack

    Note: task services is not swarm swarm services
    '''
    docker_client = docker.DockerClient(base_url=DOCKER_BASE_URL)
    services = []
    for swarm_service in docker_client.services.list():
        service_name = swarm_service.name
        labels = glom.glom(swarm_service.attrs,
                           'Spec.TaskTemplate.ContainerSpec.Labels')
        env = glom.glom(swarm_service.attrs,
                        'Spec.TaskTemplate.ContainerSpec.Env')
        for task in swarm_service.tasks():
            if not task.get('DesiredState') == 'running':
                continue
            id = task['ID']
            slot = task['Slot']
            name = f'{service_name}.{slot}.{id}'
            services.append(Service(name, labels=labels, env=env))
    return services


# def get_container_scrape_params(container):
#     '''
#     return service port and path for scrape
#     source Env = ['ENV_NAME1=VAL1', 'ENV_NAME2=VAL2', ...]
#     '''
#     envd = dict([e.split('=') for e in container.attrs['Config']['Env']])
#     port = envd.get('SCRAPE_PORT', 80)
#     path = envd.get('SCRAPE_PATH', '/metrics')
#     return port, path


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
        metrics = list(text_string_to_metric_families(response.text))
        return metrics


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


def main():
    while True:
        time.sleep(SCRAPE_INTERVAL)
        if SWARM_MODE:
            services = swarm_task_services()
        else:
            services = host_services()
        # ---
        if len(services) == 0:
            logging.info('There are no services for scrape')
            continue
        for service in services:
            logging.info(f'scrape metrics from {service.url}')
            registry = CollectorRegistry()
            registry.register(collector(service.url))
            # --- push metrics to pushgateway
            push_to_gateway(
                    PUSHGATEWAY_URL,
                    job=f'{JOB_PREFIX}-{service.name}',
                    registry=registry,
                    handler=push_gateway_handler)


if __name__ == '__main__':
    main()
