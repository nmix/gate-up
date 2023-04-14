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

`PUSHGATEWAY_URL` - pushgateway url for post matrics, default `http://pushgateway:9091`

`PUSHGATEWAY_BASIC_AUTH_USERNAME` - basic auth username on pushgateway, default `""`

`PUSHGATEWAY_BASIC_AUTH_PASSWORD` - basic auth password on pushgateway, default `""`

`SCRAPE_INTERVAL` - scrape period in seconds, default 5s


target service environment variables:

`SCRAPE_PORT` - port for scrape metrics, default: 80

`SCRAPE_PATH` - path for scrape metrics, default: /metrics

## Run from source

```bash
curl -sSL https://install.python-poetry.org | python3 -
git clone https://github.com/nmix/gate-up.git

cd gate-up
docker-compose up -d
```

Open pushgateway page on *localhost:9091* with login **admin** and password **admin**.


## Prometheus with Basic Auth

Use `PUSHGATEWAY_*` vars in app compose section for push metrics to pushgateway with enabled basic auth.

```yaml
environment:
  PUSHGATEWAY_URL: http://pc-ip-address:19091
  PUSHGATEWAY_BASIC_AUTH_USERNAME: admin
  PUSHGATEWAY_BASIC_AUTH_PASSWORD: admin
```

![gate-up pushgateway example](https://clck.ru/32Nh4Y)


