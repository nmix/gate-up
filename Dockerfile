FROM python:3.11-slim

ENV PATH /opt/venv/bin:$PATH
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN python -m venv venv && \
    pip install --no-cache-dir poetry==1.4.2

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root --only main

COPY . .

ENTRYPOINT ["python"]
CMD ["app.py"]
