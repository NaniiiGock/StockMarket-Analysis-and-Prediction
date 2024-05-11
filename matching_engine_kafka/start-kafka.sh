#!/bin/bash

# Wait for Zookeeper to be ready
echo "Waiting for Zookeeper to be ready..."
while ! nc -z zookeeper 6181; do
  sleep 1
done
echo "Zookeeper is ready."

# Start Kafka server
/etc/confluent/docker/run &

# Wait for Kafka to be ready
echo "Waiting for Kafka to start up..."
sleep 10

kafka-topics --create --topic orders --partitions 3 --replication-factor 1 --if-not-exists --bootstrap-server localhost:6003

# Wait for Kafka to continue running
wait
