# --- intermediate container
#     install pipenv, create requirements.txt
FROM python:3.10.4-alpine3.15 as base

RUN pip install --no-cache-dir pipenv==2022.9.24

ENV PROJECT_DIR /tmp
WORKDIR ${PROJECT_DIR}

COPY Pipfile Pipfile.lock ${PROJECT_DIR}/

RUN pipenv requirements > requirements.txt

# --- runtime container
#     install packages from requirements.txt
FROM base

ENV PROJECT_DIR /app
WORKDIR ${PROJECT_DIR}

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .

CMD ["python", "app.py"]
