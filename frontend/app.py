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
    'HNT': [],
    'SOL': [],
    'soLINK': [],
    'TBTC': [],
    'Bonk': [],
    'W': [],
}

partition_to_plot = {
    0: 'HNT',
    1: 'SOL',
    2: 'soLINK',
    3: 'TBTC',
    4: 'Bonk',
    5: 'W'
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
        for message in consumer:
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

@app.route('/data_for_HNT')
def data_for_HNT():
    return jsonify({'labels': list(range(len(data_store['HNT']))), 'values': data_store['HNT']})

@app.route('/data_for_SOL')
def data_for_SOL():
    return jsonify({'labels': list(range(len(data_store['SOL']))), 'values': data_store['SOL']})

@app.route('/data_for_soLINK')
def data_for_soLINK():
    return jsonify({'labels': list(range(len(data_store['soLINK']))), 'values': data_store['soLINK']})

@app.route('/data_for_TBTC')
def data_for_TBTC():
    return jsonify({'labels': list(range(len(data_store['TBTC']))), 'values': data_store['TBTC']})

@app.route('/data_for_Bonk')
def data_for_Bonk():
    return jsonify({'labels': list(range(len(data_store['Bonk']))), 'values': data_store['Bonk']})

@app.route('/data_for_W')
def data_for_W():
    return jsonify({'labels': list(range(len(data_store['W']))), 'values': data_store['W']})

####################################################################################################
#                           START THE APP
####################################################################################################

if __name__ == '__main__':
    executor.submit(start_async_tasks)
    app.run(host='0.0.0.0', port=8080, debug=True)

