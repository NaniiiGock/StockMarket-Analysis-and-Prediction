CREATE TABLE IF NOT EXISTS matched_orders (
    id SERIAL PRIMARY KEY,
    buy_order_id INTEGER,
    sell_order_id INTEGER,
    item VARCHAR(255),
    price NUMERIC,
    quantity NUMERIC
);