# Gate UP

Metrics translator from services to pushgateway.

## About

Let's say we have some scaled worker services in docker-compose and
each of them have own metrics.
We need to take metrics from each service and transfer them to prometheus
via pushgateway.

## Quickstart

1) add gateup service to compose file and mount docker.sock file

2) add pushgateway service or use `PUSHGATEWAY_URL` environment variable

3) set "com.github.nmix.gate-up.scrape" label and `SCRAPE_PORT` variable to target service

```yml
services:
  worker:
    scale: 2
    expose:
      - 9100
    labels:
      - "com.github.nmix.gate-up.scrape"
    environment:
      SCRAPE_PORT: 9100

  gateup:
    image: zoidenberg/gate-up:latest
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro

  pushgateway:
    image: prom/pushgateway
    container_name: pushgateway
    ports:
      - 9091:9091
```

gateup environment variables:

`PUSHGATEWAY_URL` - pushgateway url for post matrics
`SCRAPE_INTERVAL` - scrape period in seconds, default 5s

target service environment variables:
`SCRAPE_PORT` - port for scrape metrics, default: 80
`SCRAPE_PATH` - path for scrape metrics, default: /metrics
