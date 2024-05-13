from flask import Flask, render_template, request, redirect, url_for, jsonify
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from aiokafka import AIOKafkaConsumer
import json
from flask import Flask, render_template, request, jsonify
import requests
from kafka import KafkaProducer
import json
import time

executor = ThreadPoolExecutor(1)

app = Flask(__name__)
users = {}

user_id = None

data_store = {
    'HNT': [],
    'SOL': [],
    'soLINK': [],
    'TBTC': [],
    'Bonk': [],
    'W': [],
}
data_store_times={
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
#                           SPARK
#================================================================================================

# from pyspark.sql import SparkSession
# from pyspark.sql.functions import from_json, col
# from flask import Flask, jsonify, render_template
# import threading

# app = Flask(__name__)
# data_store = {
#     'HNT': [],
#     'SOL': [],
#     'soLINK': [],
#     'TBTC': [],
#     'Bonk': [],
#     'W': []
# }

# spark = SparkSession.builder \
#     .appName("KafkaSparkIntegration") \
#     .master("local[*]") \
#     .getOrCreate()

# def consume_from_kafka():
#     df = spark \
#         .readStream \
#         .format("kafka") \
#         .option("kafka.bootstrap.servers", "localhost:9092") \
#         .option("subscribe", "prices") \
#         .option("startingOffsets", "earliest") \
#         .load()

#     schema = "value STRING, partition INT"  # Adjust schema as per your data
#     df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

#     query = df \
#         .writeStream \
#         .foreachBatch(process_batch) \
#         .start()
    
#     query.awaitTermination()

# def process_batch(df, epoch_id):
#     if not df.isEmpty():
#         collected_data = df.collect()
#         for row in collected_data:
#             partition_key = row['partition']
#             value = row['value']
#             key = list(data_store.keys())[partition_key]  # Convert index to key name
#             data_store[key].append(value)
#             data_store[key] = data_store[key][-150:]  # Keep only last 150 entries

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
        async for message in consumer:
            # print(f"Received message: {message} on partition {message.partition}")
            if message.partition in partition_to_plot:
                data_store[partition_to_plot[message.partition]].append(message.value['value'])
                # data_store_times[partition_to_plot[message.partition]].append(message.value['datetime'])
                if len(data_store[partition_to_plot[message.partition]]) > 150:
                    data_store[partition_to_plot[message.partition]] = data_store[partition_to_plot[message.partition]][-150:]
                    # data_store_times[partition_to_plot[message.partition]] = data_store_times[partition_to_plot[message.partition]][-150:]
                # print(data_store[partition_to_plot[message.partition]])
    finally:
        await consumer.stop()

def start_async_tasks():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(consume())
    
#================================================================================================
#                           ROUTES
#================================================================================================


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    response = requests.post('http://user_info:5000/login', json={'username': username, 'password': password})
    
    if response.status_code == 200:
        data = response.json()
        user_id = data.get('user_id')
        print("Successfully logged in with user_id:", user_id)
        return redirect(url_for('data_selection'))
    else:
        return render_template('login.html', error="Login failed")

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    response = requests.post('http://user_info:5000/register', json={'username': username, 'email': email, 'password': password})
    
    if response.status_code == 201:
        user_id = response.json().get('user_id')
        print("Successfully registered user", username, "with user_id:", user_id)
        return redirect(url_for('data_selection'))
    else:
        return render_template('login.html', error="Registration failed")

@app.route('/')
def index_login_register():
    return render_template('login.html')


# =================================================================================================
#                           Historical data
# =================================================================================================
    
@app.route('/data_selection')
def data_selection():
    return render_template('data_selection.html')

@app.route('/submit', methods=['POST'])
def submit():
    start_date = request.form['startDateTime'] +":00Z"
    end_date = request.form['endDateTime'] + ":00Z"
    currencies = request.form.getlist('currencies')
    print("=====================================")
    print("start_date: ", start_date)
    print("end_date: ", end_date)   
    print("currencies: ", currencies)
    print("=====================================")
    chart_data = parse_data(start_date, end_date, currencies[-1])
    return jsonify(chart_data)

def parse_data(start_date, end_date, currencies):    
    api_url = f"http://stock_api:3000/price/interval?id={currencies}&vsToken=USDT&start_time={start_date}&end_time={end_date}"
    print("API url ", api_url)
    response = requests.get(api_url)

    print("response:" , response.json())
    labels = [point['datetime'] for point in response.json()][::-1] 
    values = [point['value'] for point in response.json()][::-1]
    return {
        'labels': labels, 
        'values': values 
    }

# =================================================================================================
#                           Streaming
# =================================================================================================


@app.route('/plot-list')
def plot_list():
    return render_template('plot_list.html')
    
    

@app.route('/data_for_HNT')
def data_for_HNT():
    # labels = [x[0] for x in data_store_2['HNT']]
    # values = [x[1] for x in data_store_2['HNT']]
    # labels = [list(data.keys())[0] for data in data_store_2['HNT']]
    # values = [list(data.values())[0] for data in data_store_2['HNT']]
    # return jsonify({'labels': labels, 'values': values})
    return jsonify({'labels': list(range(len(data_store['HNT']))), 'values': data_store['HNT']})


# @app.route('/data_for_SOL')
# def data_for_SOL():
#     # Extract labels and values assuming data_store['SOL'] is a list of tuples (datetime, value)
#     labels = [date_str for date_str in data_store_times['SOL']]
#     values = [value for _, value in data_store['SOL']]
#     return jsonify({'labels': labels, 'values': values})

@app.route('/data_for_SOL')
def data_for_SOL():
    return jsonify({'labels': list(range(len(data_store['SOL']))), 'values': data_store['SOL']})

@app.route('/data_for_soLINK')
def data_for_soLINK():
    # labels = [list(data.keys()) for data in data_store_2['soLINK']]
    # values = [list(data.values()) for data in data_store_2['soLINK']]
    # return jsonify({'labels': labels, 'values': values})
    return jsonify({'labels': list(range(len(data_store['soLINK']))), 'values': data_store['soLINK']})

@app.route('/data_for_TBTC')
def data_for_TBTC():
    # labels = [list(data.keys())[0] for data in data_store_2['TBTC']]
    # values = [list(data.values())[0] for data in data_store_2['TBTC']]
    # return jsonify({'labels': labels, 'values': values})
    return jsonify({'labels': list(range(len(data_store['TBTC']))), 'values': data_store['TBTC']})

@app.route('/data_for_Bonk')
def data_for_Bonk():
    # labels = [list(data.keys())[0] for data in data_store_2['Bonk']]
    # values = [list(data.values())[0] for data in data_store_2['Bonk']]
    # return jsonify({'labels': labels, 'values': values})
    return jsonify({'labels': list(range(len(data_store['Bonk']))), 'values': data_store['Bonk']})

@app.route('/data_for_W')
def data_for_W():
    # labels = [list(data.keys())[0] for data in data_store_2['W']]
    # values = [list(data.values())[0] for data in data_store_2['W']]
    # return jsonify({'labels': labels, 'values': values})
    return jsonify({'labels': list(range(len(data_store['W']))), 'values': data_store['W']})


# =================================================================================================
#                           TRANACTIONS
# =================================================================================================



currency_data = {
    # get current data from Nazar
    'HNT': 1,
    'SOL': 2,
    'soLINK': 3,
    'TBTC': 4,
    'Bonk': 5,
    'W': 6,
}



@app.route('/sell_buy', methods=['GET', 'POST'])
def sell_buy():
    message = ""
    if request.method == 'POST':
        try:
            action = request.form.get('action', type=str)
            amount = request.form.get('amount', type=float)
            user_price = request.form.get('user_price', type=float)
            currency = request.form.get('currency', type=str)
            
            producer = KafkaProducer(bootstrap_servers='matching_engine_kafka:9092')
            order = {'id': user_id, 'type': action, 'price': user_price, 'token': currency, 'quantity': amount}
            producer.send('orders', value=json.dumps(order).encode('utf-8'))
            producer.flush()
            
            if action == 'buy':
                total_cost = amount * user_price
                message = f"You sent a request to buy {amount} {currency} for {total_cost} USD.\nCheck your transaction history."
            elif action == 'sell':
                total_revenue = amount * user_price
                message = f"You sent a request to sell {amount} {currency} for {total_revenue} USD.\nCheck your transaction history."
        except Exception as e:
            message = f"Error: {str(e)}"  
    
    
    return render_template('sell_buy.html', currencies=currency_data, message=message)


# =================================================================================================
#                           MY HISTORY
# =================================================================================================

@app.route('/history_of_trades')
def history_of_trades():
    #transaction_history = requests.get('Anna's SERVICE')
    transaction_history = {
        'transactions': [
            {'type': 'buy', 'token': 'HNT', 'quantity': 10, 'price': 10, 'total': 100},\
            {'type': 'sell', 'token': 'SOL', 'quantity': 5, 'price': 20, 'total': 100},\
            {'type': 'buy', 'token': 'soLINK', 'quantity': 10, 'price': 10, 'total': 100}]}

    return render_template('history_of_trades.html', transactions=transaction_history['transactions'])


####################################################################################################
#                                           START THE APP
####################################################################################################

if __name__ == '__main__':
    executor.submit(start_async_tasks)
    app.run(host='0.0.0.0', port=8080)

