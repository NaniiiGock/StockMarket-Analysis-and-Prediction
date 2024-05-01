FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r app/requirements.txt

# Run app.py when the container launches
CMD ["python", "app.py"]
