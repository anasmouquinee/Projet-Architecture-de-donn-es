""" Silver Transformation """

import os
import re
import json
import logging
from io import BytesIO

import boto3
import pandas as pd
from langdetect import detect, LangDetectException

logger = logging.getLogger("silver_transform")


class SilverTransformer:
    """ Transform Data """

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.getenv("MINIO_ROOT_USER", "minio_admin"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "anaskaelar"),
        )

    def transform(self, date_str: str) -> int:
        """ Process Date """
        # Read Bronze
        articles = self._read_bronze(date_str)
        if not articles:
            logger.warning("No Bronze data to transform", extra={"date": date_str})
            return 0

        df = pd.DataFrame(articles)

        # Strip HTML
        df["content"] = df["content"].apply(self._strip_html)
        df["title"] = df["title"].apply(self._strip_html)

        # Normalise Text
        df["content"] = df["content"].apply(self._normalize_text)
        df["title"] = df["title"].apply(self._normalize_text)

        # Detect Language
        df["_language"] = df["content"].apply(self._detect_language)

        # Deduplicate URLs
        initial_count = len(df)
        df = df.drop_duplicates(subset=["url"], keep="first")
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.info("Duplicates removed", extra={"removed": duplicates_removed})

        # Drop HTML
        if "raw_html" in df.columns:
            df = df.drop(columns=["raw_html"])

        # Add Metadata
        df["_silver_processed_at"] = pd.Timestamp.utcnow().isoformat()

        # Save Parquet
        self._write_silver(df, date_str)

        logger.info(
            {"date": date_str, "count": len(df)},
            "Silver transformation completed"
        )
        return len(df)

    def _read_bronze(self, date_str: str) -> list[dict]:
        """ Read JSON """
        articles = []
        paginator = self.s3_client.get_paginator("list_objects_v2")

        # Search Sources
        for page in paginator.paginate(Bucket="bronze", Prefix=f"source="):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if f"date={date_str}" in key and key.endswith(".json"):
                    try:
                        response = self.s3_client.get_object(Bucket="bronze", Key=key)
                        article = json.loads(response["Body"].read().decode("utf-8"))
                        article["_bronze_path"] = key
                        articles.append(article)
                    except Exception as error:
                        logger.error("Error reading Bronze", extra={"key": key, "error": str(error)})

        return articles

    def _write_silver(self, df: pd.DataFrame, date_str: str):
        """ Write Parquet """
        buffer = BytesIO()
        df.to_parquet(buffer, index=False, engine="pyarrow")
        buffer.seek(0)

        key = f"date={date_str}/articles.parquet"
        self.s3_client.put_object(
            Bucket="silver",
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        logger.info("Silver Parquet saved", extra={"key": key})

    @staticmethod
    def _strip_html(text: str) -> str:
        """ Remove HTML """
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r"<[^>]+>", " ", text)
        # Remove HTML entities
        clean = re.sub(r"&\w+;", " ", clean)
        return clean.strip()

    @staticmethod
    def _normalize_text(text: str) -> str:
        """ Normalise Formatting """
        if not text:
            return ""
        # Replace multiple spaces/tabs with a single space
        normalized = re.sub(r"[ \t]+", " ", text)
        # Normalise excessive newlines
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    @staticmethod
    def _detect_language(text: str) -> str:
        """ Detect Lang """
        if not text or len(text) < 20:
            return "unknown"
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"
