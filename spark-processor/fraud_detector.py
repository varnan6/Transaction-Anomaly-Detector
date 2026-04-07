import json
import os
import redis
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    BooleanType
)

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
INPUT_TOPIC = "transactions"

HIGH_AMOUNT_THRESHOLD = 800.0
VELOCITY_WINDOW_SECONDS = 60
VELOCITY_MAX_COUNT = 5
RISK_SCORE_THRESHOLD = 0.5

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("merchant_category", StringType(), True),
    StructField("merchant_name", StringType(), True),
    StructField("country", StringType(), True),
    StructField("city", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("card_last4", StringType(), True),
    StructField("is_fraud", BooleanType(), True),
    StructField("is_online", BooleanType(), True),
    StructField("device_fingerprint", StringType(), True),
])


def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5,
    )


def compute_risk_score(row, redis_client):
    score = 0.0
    reasons = []

    if row["amount"] > HIGH_AMOUNT_THRESHOLD:
        score += 0.3
        reasons.append(f"high_amount:${row['amount']:.0f}")

    user_countries_key = f"user:{row['user_id']}:countries"
    known_countries = redis_client.smembers(user_countries_key)
    if known_countries and row["country"] not in known_countries:
        score += 0.3
        reasons.append(f"foreign_country:{row['country']}")

    if row["merchant_category"] in ("atm_withdrawal", "online_retail", "electronics"):
        score += 0.2
        reasons.append(f"risky_category:{row['merchant_category']}")

    velocity_key = f"user:{row['user_id']}:velocity"
    current_velocity = redis_client.incr(velocity_key)
    if current_velocity == 1:
        redis_client.expire(velocity_key, VELOCITY_WINDOW_SECONDS)

    if current_velocity > VELOCITY_MAX_COUNT:
        score += 0.3
        reasons.append(f"high_velocity:{current_velocity}_per_min")

    if row.get("is_online") and row["amount"] > 200:
        score += 0.1
        reasons.append("online_high_amount")

    return min(score, 1.0), reasons


def process_batch(batch_df, epoch_id):
    if batch_df.isEmpty():
        return

    rows = batch_df.collect()
    print(f"Processing batch #{epoch_id} | {len(rows)} transactions")

    redis_client = get_redis_client()
    pipe = redis_client.pipeline()

    for row in rows:
        row_dict = row.asDict()
        pipe.sadd(f"user:{row_dict['user_id']}:countries", row_dict["country"])
        pipe.expire(f"user:{row_dict['user_id']}:countries", 604800)
        pipe.incrbyfloat("stats:total_volume", row_dict["amount"])
        pipe.incr("stats:total_transactions")

    pipe.execute()

    alerts = []

    for row in rows:
        row_dict = row.asDict()
        risk_score, reasons = compute_risk_score(row_dict, redis_client)
        redis_client.incr(f"stats:category:{row_dict['merchant_category']}")

        if risk_score >= RISK_SCORE_THRESHOLD:
            alerts.append({
                "transaction_id": row_dict["transaction_id"],
                "user_id": row_dict["user_id"],
                "amount": row_dict["amount"],
                "merchant_category": row_dict["merchant_category"],
                "country": row_dict["country"],
                "risk_score": round(risk_score, 3),
                "reasons": reasons,
                "detected_at": datetime.utcnow().isoformat(),
                "ground_truth_fraud": row_dict.get("is_fraud", False),
            })

    if alerts:
        pipe = redis_client.pipeline()
        for alert in alerts:
            pipe.lpush("alerts:recent", json.dumps(alert))
            pipe.ltrim("alerts:recent", 0, 499)
            pipe.incr("stats:fraud_detected")
        pipe.execute()

    redis_client.set("stats:last_batch_size", len(rows))
    redis_client.set("stats:last_batch_time", datetime.utcnow().isoformat())
    print(f"Batch #{epoch_id} done | {len(alerts)} alerts")


def main():
    spark = (
        SparkSession.builder
        .appName("FraudDetector")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_SERVERS)
        .option("subscribe", INPUT_TOPIC)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", "500")
        .load()
    )

    transactions = (
        raw_stream
        .select(
            F.from_json(F.col("value").cast("string"), TRANSACTION_SCHEMA).alias("data")
        )
        .select("data.*")
        .filter(F.col("transaction_id").isNotNull())
    )

    query = (
        transactions.writeStream
        .outputMode("append")
        .foreachBatch(process_batch)
        .trigger(processingTime="3 seconds")
        .option("checkpointLocation", "/tmp/spark-checkpoint")
        .start()
    )

    print(f"Streaming query started on topic: {INPUT_TOPIC}")
    query.awaitTermination()


if __name__ == "__main__":
    main()
