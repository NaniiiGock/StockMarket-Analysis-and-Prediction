from kafka import KafkaConsumer
import json
import redis
import threading
import os
import logging
import sys


# Set up logging to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class TradeMatchingSystem:
    def __init__(self):
        logging.info("Connecting to Kafka and Redis...")
        # Connect to Redis
        redis_node = os.getenv('REDIS_NODE', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_client = redis.RedisCluster(host=redis_node, port=redis_port)
        self.redis_client.flushdb()

        # Connect to Kafka
        self.consumer = KafkaConsumer('orders', bootstrap_servers='matching_engine_kafka:9092', group_id='my-group')

        self.matching_threads = {}  # Dictionary to store matching threads for each token

        self.logging_url = "http://user_info:2011/add_transaction"

        logging.info("Engine is Connected")

    def start(self):
        # Consume orders from Kafka
        logging.info("Starting Kafka consumer")
        for msg in self.consumer:
            order = json.loads(msg.value.decode('utf-8'))
            logging.info(f'Order: {order}')
            self.place_order(order)
            self.start_matching_for_token(order['token'])

    def place_order(self, order):
        # Store the order in Redis sorted sets based on price for each token and type
        order_key = f"{order['token']}_{order['type']}_orders"
        self.redis_client.zadd(order_key, {json.dumps(order): order['price']})

    def start_matching_for_token(self, token):
        if token not in self.matching_threads:
            matching_thread = threading.Thread(target=self.match_orders, args=(token,))
            matching_thread.daemon = True
            matching_thread.start()
            self.matching_threads[token] = matching_thread

    def match_orders(self, token):
        while True:
            buy_orders_key = f"{token}_buy_orders"
            sell_orders_key = f"{token}_sell_orders"

            # Fetch the best buy and sell orders for the specified token
            best_buy_order = self.redis_client.zrange(buy_orders_key, 0, 0, withscores=True)
            best_sell_order = self.redis_client.zrange(sell_orders_key, 0, 0, withscores=True)

            # If there are no buy or sell orders, delete thread and return
            if not best_buy_order or not best_sell_order:
                del self.matching_threads[token]
                return

            # Extract order details
            buy_order_json = best_buy_order[0][0]
            sell_order_json = best_sell_order[0][0]

            buy_order = json.loads(buy_order_json)
            sell_order = json.loads(sell_order_json)

            # Extract order details
            buy_price, buy_quantity, buy_id = buy_order["price"], buy_order["quantity"], buy_order["id"]
            sell_price, sell_quantity, sell_id = sell_order["price"], sell_order["quantity"], sell_order["id"]

            # Algorithm
            if buy_price < sell_price:
                del self.matching_threads[token]
                return

            # Remove matched orders from Redis
            self.redis_client.zrem(buy_orders_key, buy_order_json)
            self.redis_client.zrem(sell_orders_key, sell_order_json)

            if buy_quantity > sell_quantity:
                # Update buyer quantities
                new_buy_quantity = buy_quantity - sell_quantity
                updated_buy_order = json.dumps({
                    "price": buy_price,
                    "quantity": new_buy_quantity,
                    "id": buy_id,
                    "token": token,
                    "type": "buy"
                })
                self.place_order(updated_buy_order)

            elif buy_quantity < sell_quantity:
                # Update seller quantities
                new_sell_quantity = sell_quantity - buy_quantity
                updated_sell_order = json.dumps({
                    "price": sell_price,
                    "quantity": new_sell_quantity,
                    "id": sell_id,
                    "token": token,
                    "type": "sell"
                })
                self.place_order(updated_sell_order)

            logging.info(f"Matched order for {token}: Buy Order ID {buy_id} at {buy_price} USD with quantity {buy_quantity}"
                         f" matched with Sell Order ID {sell_id} at {sell_price} USD with quantity {sell_quantity}")
            self.insert_matched_order(buy_id, sell_id, item, max(buy_price, sell_price), min(buy_quantity, sell_quantity))


    def insert_matched_order(self, buy_order_id, sell_order_id, item, price, quantity):
        data = {
            "user_id_sold": sell_order_id,
            "user_id_bought": buy_order_id,
            "item": item,
            "price": price,
            "quantity": quantity
        }

        headers = {'Content-Type': 'application/json'}

        response = requests.post(self.logging_url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            print("Transaction added successfully.")
        else:
            print("Failed to add transaction. Status code:", response.status_code)


trade_matching_system = TradeMatchingSystem()
trade_matching_system.start()
