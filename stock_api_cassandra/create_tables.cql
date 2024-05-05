CREATE KEYSPACE IF NOT EXISTS prices WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' };

CREATE TABLE prices.prices
(
    "token"  text,
    datetime timestamp,
    value    double,
    PRIMARY KEY ("token", datetime)
) WITH CLUSTERING ORDER BY ("token" DESC);
