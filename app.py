"""
Scrape metrics from target services and push them to PushGateway
"""
import docker
import logging
import requests

logging.basicConfig(level="INFO")

def log(msg):
    logging.info(msg)

docker_client = docker.DockerClient(base_url="unix://tmp/docker.sock")

def current_container():
    """
    return Container instance for current app
    """
    hostname = open("/etc/hostname").readline()[:-1]
    try:
        container = docker_client.containers.get(hostname)
    except docker.errors.NotFound:
        RuntimeError("Not in docker?")
    return container


def project_containers():
    """
    return filtered list of compose project containers
    """
    return []


c = current_container()
log(c)
log(c.labels)
