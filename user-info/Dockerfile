FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r app/requirements.txt

# Run both app.py and user-history.py when the container launches
CMD ["sh", "-c", "python app.py & python user-history.py"]
