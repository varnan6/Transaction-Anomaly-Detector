# Transaction-Anomaly-Detection — Real-Time Fraud Detection

Real-time credit card fraud detection using Apache Kafka, Apache Spark Structured Streaming, Redis, FastAPI, and React. Fully containerized with Docker Compose.

## Stack

| Layer             | Technology             |
| ----------------- | ---------------------- |
| Message Broker    | Apache Kafka           |
| Stream Processing | Apache Spark (PySpark) |
| Cache / Store     | Redis                  |
| API               | FastAPI + WebSockets   |
| Dashboard         | React + Recharts       |
| Infrastructure    | Docker Compose         |

## Architecture

```
Producer → Kafka → Spark → Redis → FastAPI → React Dashboard
```

## Prerequisites

- Docker Desktop (8GB RAM allocated recommended)
- Ports 3000, 8000, 9092, 6379 available

## Getting Started

```bash
git clone https://github.com/your-username/Transaction-Anomaly-Detection.git
cd Transaction-Anomaly-Detection

docker compose up -d --build
```

Wait ~90 seconds for all services to initialize, then open:

- **Dashboard** → http://localhost:3000
- **API Docs** → http://localhost:8000/docs

## Project Structure

```
├── docker-compose.yml
├── kafka-producer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── producer.py          # Simulates transaction stream
├── spark-processor/
│   ├── Dockerfile
│   └── fraud_detector.py    # Spark Structured Streaming job
├── api-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py              # FastAPI + WebSocket server
└── dashboard/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/
        └── App.js           # React dashboard
```

## Useful Commands

```bash
# View all logs
make logs

# View logs for a specific service
make spark-logs
make producer-logs
make api-logs

# Inspect live Kafka messages
make peek-kafka

# Open Redis CLI
make redis-cli

# Check running containers
make status

# Stop (keep data)
make down

# Stop and wipe all data
make clean
```

## Fraud Detection Logic

Transactions are scored 0.0–1.0 based on weighted rules evaluated in Spark:

| Rule                              | Score |
| --------------------------------- | ----- |
| Amount > $800                     | +0.30 |
| Foreign country (unseen for user) | +0.30 |
| High-risk merchant category       | +0.20 |
| Velocity > 5 transactions/minute  | +0.30 |
| Online transaction > $200         | +0.10 |

Transactions scoring ≥ 0.5 generate a fraud alert stored in Redis and pushed to the dashboard via WebSocket.

## Environment Variables

| Variable                  | Service         | Default       | Description          |
| ------------------------- | --------------- | ------------- | -------------------- |
| `KAFKA_BOOTSTRAP_SERVERS` | producer, spark | `kafka:29092` | Kafka broker address |
| `TRANSACTIONS_PER_SECOND` | producer        | `10`          | Simulated TPS        |
| `REDIS_HOST`              | spark, api      | `redis`       | Redis hostname       |
| `REDIS_PORT`              | spark, api      | `6379`        | Redis port           |
