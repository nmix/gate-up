"""
Scrape metrics from target services and push them to PushGateway
"""
import docker
import logging
import requests

from prometheus_client.parser import text_string_to_metric_families
from prometheus_client import CollectorRegistry, push_to_gateway
from urllib.parse import urljoin

logging.basicConfig(level="INFO")

docker_client = docker.DockerClient(base_url="unix://tmp/docker.sock")

WORKING_DIR_LABEL = "com.docker.compose.project.working_dir"
SCRAPE_LABEL = "com.github.nmix.gate-up.scrape"


def log(msg):
    logging.info(msg)


def project_containers():
    """
    return list of compose project containers
    """
    # --- get current container
    hostname = open("/etc/hostname").readline()[:-1]
    try:
        app_container = docker_client.containers.get(hostname)
    except docker.errors.NotFound:
        RuntimeError("Not in docker?")
    # --- filter project containers by working project
    working_dir = app_container.labels[WORKING_DIR_LABEL]
    labels = [f"{WORKING_DIR_LABEL}={working_dir}", SCRAPE_LABEL]
    containers = docker_client.containers.list(filters={"label": labels})
    containers = [c for c in containers if c != app_container]
    return containers


def get_container_scrape_params(container):
    """
    return service port and path for scrape
    """
    envd = dict([e.split("=") for e in container.attrs["Config"]["Env"]])
    port = envd.get("SCRAPE_PORT", 80)
    path = envd.get("SCRAPE_PATH", "/metrics")
    return port, path


class collector:
    """
    Pseudo-collector class
    @see https://clck.ru/h3aEm
    """
    def __init__(self, url):
        self.url = url

    def collect(self):
        response = requests.get(self.url)
        return list(text_string_to_metric_families(response.text))


for container in project_containers():
    # --- specify the metrics url
    port, path = get_container_scrape_params(container)
    url = urljoin(f"http://{container.name}:{port}", path)
    log(f"scrape metrics from {url}")
    # ---
    registry = CollectorRegistry()
    registry.register(collector(url))
    # --- push metrics to pushgateway
    push_to_gateway('pushgateway:9091', job=container.name, registry=registry)
