import pytest
import app


@pytest.mark.parametrize(
        'name, env, url',
        [
            ('foo', [], 'http://foo:80/metrics'),
            ('bar', ['SCRAPE_PORT=9999'], 'http://bar:9999/metrics'),
            (
                'foobar',
                ['SCRAPE_PORT=8888', 'SCRAPE_PATH=/observability/metrics'],
                'http://foobar:8888/observability/metrics'
                ),
            ]
        )
def test_service_url(name, env, url):
    service = app.Service(name, env=env)
    assert service.url == url
