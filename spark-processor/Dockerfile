FROM apache/spark:3.5.1-python3

USER root

RUN pip3 install --no-cache-dir \
    redis==5.0.1 \
    numpy==1.24.4

RUN curl -L -o /opt/spark/jars/spark-sql-kafka.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar && \
    curl -L -o /opt/spark/jars/kafka-clients.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar && \
    curl -L -o /opt/spark/jars/spark-token-provider.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.1/spark-token-provider-kafka-0-10_2.12-3.5.1.jar && \
    curl -L -o /opt/spark/jars/commons-pool2.jar \
    https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

COPY fraud_detector.py /app/fraud_detector.py

WORKDIR /app

CMD ["/opt/spark/bin/spark-submit", \
     "--master", "local[2]", \
     "--conf", "spark.sql.shuffle.partitions=4", \
     "--conf", "spark.streaming.stopGracefullyOnShutdown=true", \
     "/app/fraud_detector.py"]
