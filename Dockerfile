FROM node:18 AS frontend-builder
WORKDIR /app/frontend

COPY ./frontend/ .
RUN npm install
RUN REACT_APP_API_URL="" npm run build

FROM python:3.12-slim AS python-builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.1.2
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

COPY ./api/pyproject.toml ./api/poetry.lock* ./api/
WORKDIR /app/api

RUN poetry install --no-root

COPY ./api .

RUN mkdir -p /app/api/static

COPY --from=frontend-builder /app/frontend/build/ /app/api/static/

CMD ["poetry", "run", "python", "-m", "app"]
