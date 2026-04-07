import json
import os
import random
import time
import uuid
from datetime import datetime

from faker import Faker
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

fake = Faker()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TPS = int(os.getenv("TRANSACTIONS_PER_SECOND", "5"))
TOPIC = "transactions"

MERCHANT_CATEGORIES = [
    "grocery", "restaurant", "gas_station", "online_retail",
    "travel", "entertainment", "pharmacy", "electronics",
    "clothing", "atm_withdrawal"
]

HIGH_RISK_CATEGORIES = {"atm_withdrawal", "online_retail", "electronics"}

USER_PROFILES = [
    {
        "id": f"user_{i:04d}",
        "avg_spend": random.uniform(20, 500),
        "home_country": random.choice(["US", "US", "US", "UK", "CA"])
    }
    for i in range(200)
]


def generate_transaction():
    user = random.choice(USER_PROFILES)
    is_fraud = random.random() < 0.02
    category = random.choice(MERCHANT_CATEGORIES)

    if is_fraud:
        amount = round(random.uniform(500, 5000), 2)
        country = random.choice(["RU", "NG", "CN", "BR", "US"])
        category = random.choice(list(HIGH_RISK_CATEGORIES))
    else:
        amount = round(abs(random.gauss(user["avg_spend"], user["avg_spend"] * 0.3)), 2)
        amount = max(1.0, amount)
        country = user["home_country"] if random.random() > 0.05 else fake.country_code()

    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": amount,
        "currency": "USD",
        "merchant_category": category,
        "merchant_name": fake.company(),
        "country": country,
        "city": fake.city(),
        "timestamp": datetime.utcnow().isoformat(),
        "card_last4": str(random.randint(1000, 9999)),
        "is_fraud": is_fraud,
        "is_online": category == "online_retail" or random.random() < 0.3,
        "device_fingerprint": fake.md5() if random.random() < 0.7 else None,
    }


def create_producer():
    retries = 0
    while retries < 30:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks=1,
                retries=3,
                linger_ms=10,
            )
            print(f"Connected to Kafka at {KAFKA_SERVERS}")
            return producer
        except NoBrokersAvailable:
            retries += 1
            wait = min(2 ** retries, 30)
            print(f"Kafka not ready, retrying in {wait}s... ({retries}/30)")
            time.sleep(wait)
    raise RuntimeError("Could not connect to Kafka after 30 retries")


def main():
    print(f"Starting transaction producer at {TPS} TPS")
    producer = create_producer()
    count = 0
    interval = 1.0 / TPS

    while True:
        try:
            transaction = generate_transaction()
            future = producer.send(TOPIC, value=transaction)

            if count % 50 == 0:
                record_metadata = future.get(timeout=5)
                print(
                    f"Sent #{count} | "
                    f"Partition: {record_metadata.partition} | "
                    f"{'FRAUD' if transaction['is_fraud'] else 'OK'} | "
                    f"${transaction['amount']} @ {transaction['merchant_category']}"
                )

            count += 1
            time.sleep(interval)

        except KeyboardInterrupt:
            producer.flush()
            producer.close()
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
