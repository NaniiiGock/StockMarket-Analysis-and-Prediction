CREATE KEYSPACE IF NOT EXISTS prices WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '1' };

CREATE TABLE prices.prices
(
    token_  text,
    datetime timestamp,
    value    double,
    PRIMARY KEY (token_, datetime)
) WITH CLUSTERING ORDER BY (datetime DESC);

