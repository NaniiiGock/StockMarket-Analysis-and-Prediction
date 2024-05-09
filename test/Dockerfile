FROM python:3.9-slim

RUN pip install kafka-python
COPY producer.py /producer.py

ENTRYPOINT ["python3", "/producer.py"]
