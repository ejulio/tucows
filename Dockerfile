FROM python:3.11-slim

WORKDIR /usr/tucows
COPY . .

ENV POETRY_HOME=/usr/local/
RUN apt-get update -y \
    && apt-get install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 -

RUN poetry install
