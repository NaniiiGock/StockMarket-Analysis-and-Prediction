from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(bootstrap_servers='kafka:6003')

orders = []
orders.append({'id': '1', 'type': 'buy', 'price': 100, 'token': 'BTC', 'quantity': 10})
orders.append({'id': '3', 'type': 'buy', 'price': 105, 'token': 'ETH', 'quantity': 20})
orders.append({'id': '2', 'type': 'sell', 'price': 100, 'token': 'BTC', 'quantity': 10})
orders.append({'id': '4', 'type': 'sell', 'price': 95, 'token': 'ETH', 'quantity': 20})

for order in orders:
    producer.send('orders', value=json.dumps(order).encode('utf-8'))
    print("Sent order:", order)
    time.sleep(1/25)
