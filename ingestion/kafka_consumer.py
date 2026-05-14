"""
kafka_consumer.py — Consumes articles from Kafka and writes them to Bronze (MinIO).

This consumer runs as a standalone process, listening on
the 'raw-articles' topic and saving each article to the Data Lake.
"""

import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("kafka_consumer")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_ARTICLES", "raw-articles")
KAFKA_GROUP_ID = "bronze-writer-group"


def consume_and_store():
    """
    Consumes messages from Kafka and stores them in MinIO (Bronze).
    This process runs indefinitely as a service.
    """
    try:
        from kafka import KafkaConsumer
        import boto3

        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BROKER,
            group_id=KAFKA_GROUP_ID,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

        # Connect to MinIO
        s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.getenv("MINIO_ROOT_USER", "minio_admin"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "anaskaelar"),
        )

        logger.info("Kafka consumer started, waiting for messages...")

        for message in consumer:
            article = message.value
            _store_in_bronze(s3_client, article)

    except Exception as error:
        logger.error("Error in Kafka consumer", extra={"error": str(error)})
        raise


def _store_in_bronze(s3_client, article: dict):
    """
    Stores a single article in the Bronze bucket of MinIO.

    The path follows this pattern:
    bronze/source=<source>/date=<YYYY-MM-DD>/<article_id>.json
    """
    source = article.get("source", "unknown")
    scraped_at = article.get("scraped_at", datetime.now(timezone.utc).isoformat())
    article_id = article.get("_article_id", "unknown")

    # Extract the date for partitioning
    date_str = scraped_at[:10]  # YYYY-MM-DD

    key = f"source={source}/date={date_str}/{article_id}.json"
    body = json.dumps(article, ensure_ascii=False, default=str)

    try:
        s3_client.put_object(
            Bucket="bronze",
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )
        logger.info("Article stored in Bronze", extra={"key": key})
    except Exception as error:
        logger.error("Error storing article in Bronze", extra={"key": key, "error": str(error)})


if __name__ == "__main__":
    consume_and_store()
