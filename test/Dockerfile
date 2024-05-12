FROM python:3.9-slim

WORKDIR /app

RUN pip install kafka-python
COPY . /app

ENTRYPOINT ["python3", "producer.py"]
