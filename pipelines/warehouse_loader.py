"""
warehouse_loader.py — Loads Gold data into PostgreSQL (Data Warehouse).

Reads the aggregated Parquet files from Gold and inserts/updates them
into the analytical tables of the Data Warehouse.
"""

import os
import logging
from io import BytesIO

import boto3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger("warehouse_loader")


class WarehouseLoader:
    """Loads Gold data (Parquet) into PostgreSQL."""

    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.getenv("MINIO_ROOT_USER", "minio_admin"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "anaskaelar"),
        )
        self.db_config = {
            "host": os.getenv("POSTGRES_HOST", "postgres"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "dbname": os.getenv("POSTGRES_DB", "news_warehouse"),
            "user": os.getenv("POSTGRES_USER", "warehouse_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "anaskaelar"),
        }

    def load_all(self, date_str: str):
        """Loads all Gold data for a given date into PostgreSQL."""
        conn = psycopg2.connect(**self.db_config)
        try:
            self._load_daily_stats(conn, date_str)
            self._load_top_keywords(conn, date_str)
            self._load_source_stats(conn, date_str)
            conn.commit()
            logger.info("Warehouse load completed", extra={"date": date_str})
        except Exception as e:
            conn.rollback()
            logger.error("Error loading Warehouse", extra={"error": str(e)})
            raise
        finally:
            conn.close()

    def _read_gold(self, key: str) -> pd.DataFrame:
        """Reads a Parquet file from Gold."""
        try:
            resp = self.s3.get_object(Bucket="gold", Key=key)
            return pd.read_parquet(BytesIO(resp["Body"].read()))
        except Exception:
            return pd.DataFrame()

    def _load_daily_stats(self, conn, date_str: str):
        df = self._read_gold(f"daily_stats/date={date_str}/stats.parquet")
        if df.empty:
            return
        cur = conn.cursor()
        # Upsert: insert or update if the record already exists
        sql = """
            INSERT INTO daily_stats (stat_date, source, category, country, article_count)
            VALUES %s
            ON CONFLICT (stat_date, source, category)
            DO UPDATE SET article_count = EXCLUDED.article_count
        """
        values = [
            (row.stat_date, row.source, row.category, row.country, row.article_count)
            for row in df.itertuples()
        ]
        execute_values(cur, sql, values)
        cur.close()

    def _load_top_keywords(self, conn, date_str: str):
        df = self._read_gold(f"top_keywords/date={date_str}/keywords.parquet")
        if df.empty:
            return
        cur = conn.cursor()
        sql = """
            INSERT INTO top_keywords (stat_date, keyword, frequency, source)
            VALUES %s
            ON CONFLICT (stat_date, keyword, source)
            DO UPDATE SET frequency = EXCLUDED.frequency
        """
        values = [
            (row.stat_date, row.keyword, row.frequency, None)
            for row in df.itertuples()
        ]
        execute_values(cur, sql, values)
        cur.close()

    def _load_source_stats(self, conn, date_str: str):
        df = self._read_gold(f"source_stats/date={date_str}/sources.parquet")
        if df.empty:
            return
        cur = conn.cursor()
        sql = """
            INSERT INTO source_stats (source, country, total_articles)
            VALUES %s
            ON CONFLICT (source)
            DO UPDATE SET total_articles = source_stats.total_articles + EXCLUDED.total_articles
        """
        values = [
            (row.source, row.country, row.total_articles)
            for row in df.itertuples()
        ]
        execute_values(cur, sql, values)
        cur.close()
