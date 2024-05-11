from flask import Flask, render_template, request, redirect, url_for, jsonify
import random
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from aiokafka import AIOKafkaConsumer
import json

executor = ThreadPoolExecutor(1)

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


#================================================================================================
#                           KAFKA
#================================================================================================

# async def consume_kafka_messages(topic, kafka_server, partitions):
#     consumer = AIOKafkaConsumer(
#         bootstrap_servers=kafka_server
#     )
#     await consumer.start()
#     try:
#         topic_partitions = [TopicPartition(topic, p) for p in partitions[:-1]]
#         consumer.assign(topic_partitions)
#         async for msg in consumer:
#             message_value = msg.value.decode('utf-8')
#             print(f"Received from Kafka (Partition {msg.partition}): {message_value}")
#             data_point = json.loads(message_value)
#             plot_name = partition_to_plot.get(msg.partition)
#             if plot_name and 'value' in data_point:
#                 data_store[plot_name].append(data_point['value'])
#     finally:
#         await consumer.stop()

# def start_kafka_consumer():
#     kafka_topic = 'prices'
#     kafka_server = 'stock_api_kafka:9092'
#     partitions = [0, 1, 2, 3, 4]
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     loop.create_task(consume_kafka_messages(kafka_topic, kafka_server, partitions))


# from kafka import KafkaConsumer
# import json

# # Create a KafkaConsumer
# consumer = KafkaConsumer(
#     'your_topic_name',
#     bootstrap_servers=['localhost:9092'],
#     auto_offset_reset='earliest',  # Start reading at the earliest message
#     enable_auto_commit=True,       # Automatically commit the offsets
#     group_id='my-group',           # Consumer group ID
#     value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # Deserializer for JSON data
# )

# # Consume messages
# for message in consumer:
#     print(f"Received message: {message.value} on partition {message.partition}")

# # Always close the consumer connection explicitly when done
# consumer.close()


# async def consume():
#     consumer = AIOKafkaConsumer(
#         'prices',
#         bootstrap_servers='stock_api_kafka:9092',
#         group_id="my-group",
#         auto_offset_reset='earliest',
#         session_timeout_ms=30000,
#         value_deserializer=lambda x: json.loads(x.decode('utf-8')), 
#         heartbeat_interval_ms=3000
#     )
#     await consumer.start()
#     try:
#         async for message in consumer:
#             print(f"Received message: {message.value} on partition {message.partition}")
#             plot_name = partition_to_plot[message.partition]
#             data_store[plot_name].append(message.value['value'])
#             print(data_store[plot_name])
#     finally:
#         await consumer.stop()
        
async def consume():

    consumer = AIOKafkaConsumer(
        'prices',
        bootstrap_servers='stock_api_kafka:9092',
        group_id="my-group",
        auto_offset_reset='earliest',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    await consumer.start()
    try:
        async for message in consumer:
            print(f"Received message: {message.value} on partition {message.partition}")
            if message.partition in partition_to_plot:
                data_store[partition_to_plot[message.partition]].append(message.value['value'])
                print(data_store[partition_to_plot[message.partition]])
    finally:
        await consumer.stop()

def start_async_tasks():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(consume())
    
#================================================================================================
#                           ROUTES
#================================================================================================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users[username] = password
        #### here I pass data to servvice with logging to chech if user is in database####
        return redirect(url_for('data_selection'))
    return render_template('login.html')

@app.route('/data-selection')
def data_selection():
    return render_template('data_selection.html')

@app.route('/history-of-trades')
def history_of_trades():
    return render_template('history_of_trades.html')

# =================================================================================================
#                           PLOTS
# =================================================================================================


@app.route('/plot-list')
def plot_list():
    return render_template('plot_list.html')

@app.route('/data-for-plot1')
def data_for_plot1():
    new_data = random.randint(0, 50)
    data_store['plot1'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot1']))), 'values': data_store['plot1']})

@app.route('/data-for-plot2')
def data_for_plot2():
    new_data = random.randint(0, 50)
    data_store['plot2'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot2']))), 'values': data_store['plot2']})

@app.route('/data-for-plot3')
def data_for_plot3():
    new_data = random.randint(0, 50)
    data_store['plot3'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot3']))), 'values': data_store['plot3']})

@app.route('/data-for-plot4')
def data_for_plot4():
    new_data = random.randint(0, 50)
    data_store['plot4'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot4']))), 'values': data_store['plot4']})

@app.route('/data-for-plot5')
def data_for_plot5():
    new_data = random.randint(0, 50)
    data_store['plot5'].append(new_data)
    return jsonify({'labels': list(range(len(data_store['plot5']))), 'values': data_store['plot5']})

####################################################################################################
#                           START THE APP
####################################################################################################

if __name__ == '__main__':
    # start_kafka_consumer()
    executor.submit(start_async_tasks)
    app.run(host='0.0.0.0', port=8080, debug=True)
    # asyncio.run(consume())
    
