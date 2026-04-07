.PHONY: up down clean rebuild logs producer-logs spark-logs api-logs status peek-kafka redis-cli redis-stats

up:
	docker compose up -d --build

down:
	docker compose down

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

rebuild:
	docker compose up -d --build $(SERVICE)

logs:
	docker compose logs -f

producer-logs:
	docker compose logs -f producer

spark-logs:
	docker compose logs -f spark-processor

api-logs:
	docker compose logs -f api-server

status:
	docker compose ps

peek-kafka:
	docker exec -it kafka kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic transactions \
		--from-beginning \
		--max-messages 5

redis-cli:
	docker exec -it redis redis-cli

redis-stats:
	docker exec redis redis-cli MGET \
		stats:total_transactions \
		stats:fraud_detected \
		stats:total_volume
