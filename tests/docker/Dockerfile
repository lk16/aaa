FROM python:3.10

ENV AAA_TESTS_CONTAINER=1

RUN apt-get update && \
    apt-get install -y gdb valgrind

RUN pip install --upgrade pip && \
    pip install 'poetry==1.2.2'

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction

COPY stdlib /app/stdlib
COPY aaa /app/aaa
COPY c /app/c
COPY tests /app/tests

ENV AAA_STDLIB_PATH=/app/stdlib

CMD python tests/docker/run.py
