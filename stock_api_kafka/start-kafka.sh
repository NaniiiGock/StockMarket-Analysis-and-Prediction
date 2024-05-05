#!/bin/bash

# Wait for Zookeeper to be ready
echo "Waiting for Zookeeper to be ready..."
while ! nc -z zookeeper 2181; do
  sleep 1
done
echo "Zookeeper is ready."

# Start Kafka server
/etc/confluent/docker/run &

# Wait for Kafka to be ready
echo "Waiting for Kafka to start up..."
sleep 10

# Create a topic
kafka-topics --create --topic prices --partitions 6 --replication-factor 1 --if-not-exists --bootstrap-server localhost:2003

# Wait for Kafka to continue running
wait
