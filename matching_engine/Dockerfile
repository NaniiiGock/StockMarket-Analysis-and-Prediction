FROM python:3.9-slim

RUN apt-get update
RUN pip3 install --upgrade pip
WORKDIR /app

RUN pip install kafka-python
RUN pip install redis
RUN pip install sqlalchemy
RUN pip install psycopg2-binary
COPY . /app

ENTRYPOINT ["python3", "engine.py"]
