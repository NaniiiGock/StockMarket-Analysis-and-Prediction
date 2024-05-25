from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_json, window, avg
from pyspark.sql.types import StructType, StructField, StringType, FloatType, TimestampType
import signal
import sys

# Initialize Spark session
spark = SparkSession.builder \
    .appName("KafkaSparkStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0") \
    .config("spark.sql.streaming.checkpointLocation", "/opt/app/spark-checkpoint") \
    .getOrCreate()

# Define schema for incoming JSON data
schema = StructType([
    StructField("token", StringType(), True),
    StructField("value", FloatType(), True),
    StructField("datetime", TimestampType(), True)
])

# Kafka configurations
kafka_server = "stock_api_kafka:9092"
input_topic = "prices"
output_topic = "processed_prices"

# Read from Kafka topic
input_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("subscribe", input_topic) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# Parse JSON data
parsed_df = input_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# Calculate 5-second windowed average
windowed_avg_df = parsed_df \
    .withWatermark("datetime", "5 seconds") \
    .groupBy(window(col("datetime"), "5 seconds"), col("token")) \
    .agg(avg("value").alias("average_value"))

# Prepare output DataFrame to send to Kafka
output_df = windowed_avg_df.selectExpr(
    "to_json(struct(*)) AS value"
)

# Write to Kafka topic
query = output_df.writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_server) \
    .option("topic", output_topic) \
    .option("checkpointLocation", "/opt/app/kafka_checkpoint") \
    .start()


# Signal handler to gracefully stop the streaming query
def signal_handler(signal, frame):
    query.stop()
    spark.stop()
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

query.awaitTermination()
