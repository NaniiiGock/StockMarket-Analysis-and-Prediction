from flask import Flask, render_template, request, redirect, url_for
from flask import jsonify
import random
import httpx
import asyncio
import json
from aiokafka import AIOKafkaConsumer, TopicPartition

app = Flask(__name__)
users = {}

data_store = {
    'plot1': [],
    'plot2': [],
    'plot3': [],
    'plot4': [],
    'plot5': []
}

partition_to_plot = {
    0: 'plot1',
    1: 'plot2',
    2: 'plot3',
    3: 'plot4',
    4: 'plot5'
}

tokens_url = 'http://stock_api:3000/tokens'

async def fetch_tokens(retries=10, delay=5):
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.get(tokens_url)
                response.raise_for_status()
                print(response.json())
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as ex:
                print(f"Attempt {attempt + 1}/{retries} failed: {ex}")
                if attempt + 1 == retries:
                    raise
                await asyncio.sleep(delay)
        return []



currency_list = asyncio.run(fetch_tokens())

async def consume_kafka_messages(topic, kafka_server, partitions):
    consumer = AIOKafkaConsumer(
        bootstrap_servers=kafka_server
    )
    await consumer.start()
    try:
        topic_partitions = [TopicPartition(topic, p) for p in partitions[:-1]]
        consumer.assign(topic_partitions)
        async for msg in consumer:
            message_value = msg.value.decode('utf-8')
            print(f"Received from Kafka (Partition {msg.partition}): {message_value}")
            data_point = json.loads(message_value)
            plot_name = partition_to_plot.get(msg.partition)
            if plot_name and 'value' in data_point:
                data_store[plot_name].append(data_point['value'])
    finally:
        await consumer.stop()

def start_kafka_consumer():
    kafka_topic = 'prices'
    kafka_server = 'stock_api_kafka:9092'
    partitions = [0, 1, 2, 3, 4]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(consume_kafka_messages(kafka_topic, kafka_server, partitions))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users[username] = password
        #### here I pass data to servvice with logging to chech if user is in database####
        return redirect(url_for('data_selection'))
    return render_template('login.html')

if __name__ == '__main__':
    start_kafka_consumer()
    app.run(host='0.0.0.0', port=8080, debug=True)
