from kafka import KafkaConsumer
import json
import redis
import threading
import os
from sqlalchemy import create_engine


db_name = 'database'
db_user = 'username'
db_pass = 'secret'
db_host = 'db'
db_port = '6432'


class TradeMatchingSystem:
    def __init__(self):
        print("Connecting to Kafka and Redis...")
        # Connect to Redis
        redis_node = os.getenv('REDIS_NODE', 'localhost')
        self.redis_client = redis.StrictRedis(host=redis_node, port=6379)
        self.redis_client.flushdb()

        # Initialize your PostgreSQL connection
        db_string = 'postgresql://{}:{}@{}:{}/{}'.format(db_user, db_pass, db_host, db_port, db_name)
        self.db = create_engine(db_string)

        # Connect to Kafka
        self.consumer = KafkaConsumer('orders', bootstrap_servers='localhost:6003')
        # auto_offset_reset='earliest', group_id='my-group'

        self.matching_threads = {}  # Dictionary to store matching threads for each item

        print("Engine is Connected")

    def insert_matched_order(self, buy_order_id, sell_order_id, item, price, quantity):
        sql = """INSERT INTO matched_orders (buy_order_id, sell_order_id, item, price, quantity) 
                 VALUES (%s, %s, %s, %s, %s)"""
        data = (buy_order_id, sell_order_id, item, price, quantity)
        self.db.execute(sql, data)

    def start(self):
        # Consume orders from Kafka
        print("Starting Kafka consumer")
        for msg in self.consumer:
            order = json.loads(msg.value.decode('utf-8'))
            print("Order:", order)
            self.place_order(order)
            self.start_matching_for_item(order['item'])

    def place_order(self, order):
        # Store the order in Redis sorted sets based on price for each token and type
        item_key = f"{order['token']}_{order['type']}_orders"
        self.redis_client.zadd(item_key, {json.dumps(order): order['price']})

    def start_matching_for_item(self, item):
        if item not in self.matching_threads:
            matching_thread = threading.Thread(target=self.match_orders, args=(item,))
            matching_thread.daemon = True
            matching_thread.start()
            self.matching_threads[item] = matching_thread

    def match_orders(self, item):
        while True:
            buy_orders_key = f"{item}_buy_orders"
            sell_orders_key = f"{item}_sell_orders"

            # Fetch the best buy and sell orders for the specified item
            best_buy_order = self.redis_client.zrange(buy_orders_key, 0, 0, withscores=True)
            best_sell_order = self.redis_client.zrange(sell_orders_key, 0, 0, withscores=True)

            # If there are no buy or sell orders, delete thread and return
            if not best_buy_order or not best_sell_order:
                del self.matching_threads[item]
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
                del self.matching_threads[item]
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
                    "token": item,
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
                    "token": item,
                    "type": "sell"
                })
                self.place_order(updated_sell_order)

            print(f"Matched order for {item}: Buy Order ID {buy_id} at {buy_price} USD with quantity {buy_quantity}"
                  f" matched with Sell Order ID {sell_id} at {sell_price} USD with quantity {sell_quantity}")

            self.insert_matched_order(buy_id, sell_id, item, max(buy_price, sell_price), min(buy_quantity, sell_quantity))


trade_matching_system = TradeMatchingSystem()
trade_matching_system.start()
