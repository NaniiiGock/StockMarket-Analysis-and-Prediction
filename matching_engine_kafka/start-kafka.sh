#!/bin/bash

#sleep 7
#kafka-topics.sh --create --bootstrap-server kafka-server:6001 --replication-factor 1 --partitions 3 --topic orders

# Wait for Zookeeper to be ready
echo "Waiting for Zookeeper to be ready..."
while ! nc -z matching_engine_zookeeper 2181; do
  sleep 1
done
echo "Zookeeper is ready."

# Start Kafka server
/etc/confluent/docker/run &

# Wait for Kafka to be ready
echo "Waiting for Kafka to start up..."
sleep 10

kafka-topics --create --topic orders --partitions 6 --replication-factor 1 --if-not-exists --bootstrap-server localhost:9092

# Wait for Kafka to continue running
wait
