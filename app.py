"""
Scrape metrics from target services and push them to PushGateway
"""
import docker
import logging
import os
import requests

logging.basicConfig(level="INFO")

def log(msg):
    logging.info(msg)

docker_client = docker.DockerClient(base_url="unix://tmp/docker.sock")

WORKING_DIR_LABEL = "com.docker.compose.project.working_dir"
SCRAPE_LABEL = "com.github.nmix.gate-up.scrape"


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
    containers = docker_client.containers.list(
            filters={"label": [f"{WORKING_DIR_LABEL}={working_dir}", SCRAPE_LABEL]}
            )
    containers = [ c for c in containers if c != app_container ]
    return containers

def get_container_scrape_params(container):
    """
    return service port and path for scrape
    """
    envd = dict([ e.split("=") for e in container.attrs["Config"]["Env"] ])
    port = envd.get("SCRAPE_PORT", 80)
    path = envd.get("SCRAPE_PATH", "/metrics")
    return port, path

for container in project_containers():
    log(container.name)
    port, path = get_container_scrape_params(container)
    response = requests.get(os.path.join(f"http://{container.name}:{port}", path))
    log(response.text[:200])
