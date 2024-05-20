import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from confluent_kafka import Consumer
from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for, session
from dateutil import parser

app = Flask(__name__)
app.secret_key = os.urandom(24)

tokens_url = 'http://stock_api:3000/tokens'


def fetch_tokens(retries=10, delay=5):
    with requests.Session() as client:
        for attempt in range(retries):
            try:
                response = client.get(tokens_url)
                response.raise_for_status()
                print(response.json())
                return response.json()
            except (requests.RequestException, requests.HTTPError) as ex:
                print(f"Attempt {attempt + 1}/{retries} failed: {ex}")
                if attempt + 1 == retries:
                    raise
                time.sleep(delay)
        return []


currency_list = fetch_tokens()


# ================================================================================================
#                           KAFKA
# ================================================================================================

data_store = {x: [] for x in currency_list}

plot_volume = 10


def consume(token_to_get: str):
    conf = {
        'bootstrap.servers': "stock_api_kafka:9092",
        'group.id': "my-group",
        'auto.offset.reset': 'latest'
    }

    consumer = Consumer(conf)
    consumer.subscribe(['prices'])

    try:
        while True:
            message = consumer.poll(timeout=10.0)
            if message is None:
                continue
            if message.error():
                print(f"Kafka Error: {message.error}")
                continue

            current_time = datetime.now(timezone.utc)
            time_difference = timedelta(seconds=5)

            value = json.loads(message.value().decode('utf-8'))
            token = value['token']
            message_datetime = parser.isoparse(value['datetime'])

            if not (current_time - time_difference <= message_datetime <= current_time + time_difference):
                continue

            if token not in data_store:
                data_store[token] = []
            data_store[token].append((value['value'], value['datetime']))

            if token_to_get == token:
                break

    finally:
        consumer.close()


# ================================================================================================
#                           ROUTES
# ================================================================================================

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    response = requests.post('http://user_info:5000/login', json={'username': username, 'password': password})

    if response.status_code == 200:
        data = response.json()
        session['user_id'] = data.get('user_id')
        app.logger.info(f"Successfully logged in with user_id: {session['user_id']}")
        return redirect(url_for('data_selection'))
    else:
        return render_template('login.html', error="Login failed")


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    response = requests.post('http://user_info:5000/register',
                             json={'username': username, 'email': email, 'password': password})

    if response.status_code == 201:
        data = response.json()
        session['user_id'] = data.get('user_id')
        return redirect(url_for('data_selection'))
    else:
        return render_template('login.html', error="Registration failed")


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # remove user_id from session
    return redirect(url_for('login'))


@app.route('/')
def index_login_register():
    return render_template('login.html')


# =================================================================================================
#                           Historical data
# =================================================================================================

@app.route('/data_selection')
def data_selection():
    return render_template('data_selection.html', currencies=currency_list)


@app.route('/submit', methods=['POST'])
def submit():
    start_date = request.form['startDateTime'] + ":00Z"
    end_date = request.form['endDateTime'] + ":00Z"
    currencies = request.form.getlist('currency')
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

    print("response:", response.json())
    labels = [point['datetime'] for point in response.json()][::-1]
    values = [point['value'] for point in response.json()][::-1]
    return {'labels': labels, 'values': values}


# =================================================================================================
#                           Streaming
# =================================================================================================


@app.route('/streaming')
def streaming():
    return render_template('streaming.html', currencies=currency_list)


@app.route('/submit_realtime', methods=['GET'])
def submit_realtime():
    for token in currency_list:
        if len(data_store[token]) > plot_volume:
            data_store[token] = data_store[token][-plot_volume:]

    token = request.args.get('token')
    consume(token)

    values = [value[0] for value in data_store[token]]
    labels = [value[1] for value in data_store[token]]

    return jsonify({'labels': labels, 'values': values})


# =================================================================================================
#                           TRANSACTIONS
# =================================================================================================


currency_data = {  # get current data from Nazar
    'HNT': 1, 'SOL': 2, 'soLINK': 3, 'TBTC': 4, 'Bonk': 5, 'W': 6, }


@app.route('/sell_buy', methods=['GET', 'POST'])
def sell_buy():
    message = ""
    if request.method == 'POST':
        try:
            action = request.form.get('action', type=str)
            amount = request.form.get('amount', type=float)
            user_price = request.form.get('user_price', type=float)
            currency = request.form.get('currency', type=str)
            user_id = session.get('user_id', None)

            producer = KafkaProducer(bootstrap_servers='matching_engine_kafka:9092')
            order = {'id': user_id, 'type': action, 'price': user_price, 'token': currency, 'quantity': amount}
            producer.send('orders', value=json.dumps(order).encode('utf-8'))
            producer.flush()
            app.logger.info(f"Order sent: {order}")

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
    user_id = session.get('user_id')
    if not user_id:
        return "User not logged in", 401  # Handling case where no user is logged in

    url = f"http://user_info:5001/user_transactions/{user_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        transaction_data = response.json()

        # Assuming the response structure matches what you've shown in the curl example
        transactions = []
        for txn in transaction_data['transactions']:
            transactions.append({'type': 'buy' if txn['action'].lower() == 'bought' else 'sell', 'token': txn['item'],
                                 'quantity': txn['quantity'], 'price': txn['price'],
                                 'total': txn['price'] * txn['quantity']})

        return render_template('history_of_trades.html', transactions=transactions)
    except requests.RequestException as e:
        app.logger.error(f"Error fetching transactions: {str(e)}")
        return f"Error fetching transactions: {str(e)}", 500
    except KeyError:
        app.logger.error(f"Error parsing transaction data")
        print()
        return "Error processing transaction data", 500


####################################################################################################
#                                           START THE APP
####################################################################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
