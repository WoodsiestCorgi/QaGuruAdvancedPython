FROM python:3.13
LABEL authors="Max"

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 - && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /code

COPY pyproject.toml /code/pyproject.toml

RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY ./micro_service /code/micro_service

CMD ["uvicorn", "micro_service.main:app", "--host", "0.0.0.0", "--port", "80"]
