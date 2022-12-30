FROM python:3.10

ENV AAA_TESTS_CONTAINER=1

RUN pip install --upgrade pip && \
    pip install 'poetry==1.2.2'

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction

COPY tests /app/tests
COPY aaa /app/aaa
COPY stdlib /app/stdlib
COPY c /app/c

ENV AAA_STDLIB_PATH=/app/stdlib

CMD python tests/docker/run.py
