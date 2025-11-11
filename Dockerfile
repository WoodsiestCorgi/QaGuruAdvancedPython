FROM python:3.13
LABEL authors="Max"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./micro_service /code/micro_service

CMD ["fastapi", "run", "micro_service/main.py", "--port", "80"]
