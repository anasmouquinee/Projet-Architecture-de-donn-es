""" Scraper Base """

import time
import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s \u2014 %(message)s"
)


class BaseScraper(ABC):
    """ Base Class """

    # Required Fields
    REQUIRED_FIELDS = ["title", "content", "url", "source"]

    def __init__(
        self,
        source_name: str,
        base_url: str,
        rate_limit_seconds: float = 2.0,
        max_retries: int = 3,
        timeout: int = 15,
    ):
        self.source_name = source_name
        self.base_url = base_url
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(source_name)

        # HTTP Session
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8,fr;q=0.7",
        })

    # Abstract Methods

    @abstractmethod
    def get_article_urls(self) -> list[str]:
        """ Get URLs """
        pass

    @abstractmethod
    def parse_article(self, url: str, soup: BeautifulSoup) -> Optional[dict]:
        """ Parse HTML """
        pass

    # Scraping Engine

    def scrape_all(self) -> list[dict]:
        """ Run Scraping """
        self.logger.info("Starting scraping")
        articles = []

        # Get URLs
        try:
            urls = self.get_article_urls()
            self.logger.info("URLs found", extra={"url_count": len(urls)})
        except Exception as error:
            self.logger.error("Error fetching URLs", extra={"error": str(error)})
            return articles

        # Parse Articles
        for url in urls:
            article = self._scrape_single_article(url)
            if article is not None:
                articles.append(article)

            # Rate Limiting
            time.sleep(self.rate_limit_seconds)

        self.logger.info(
            "Scraping completed",
            extra={"total_scraped": len(articles), "total_urls": len(urls)}
        )
        return articles

    def _scrape_single_article(self, url: str) -> Optional[dict]:
        """ Fetch Article """
        html = self._fetch_with_retries(url)
        if html is None:
            return None

        try:
            soup = BeautifulSoup(html, "lxml")
            article = self.parse_article(url, soup)

            if article is None:
                self.logger.warning("Parse returned None", extra={"url": url})
                return None

            # Article Metadata
            article["source"] = self.source_name
            article["url"] = url
            article["scraped_at"] = datetime.now(timezone.utc).isoformat()
            article["raw_html"] = html
            article["_article_id"] = self._generate_article_id(url)

            # Validate Schema
            if self._validate_article(article):
                return article

            return None

        except Exception as error:
            self.logger.error("Error parsing article", extra={"url": url, "error": str(error)})
            return None

    # HTTP Retries

    def _fetch_with_retries(self, url: str) -> Optional[str]:
        """ Retry Download """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text

            except requests.RequestException as error:
                wait_time = 2 ** attempt
                if attempt < self.max_retries:
                    time.sleep(wait_time)

        self.logger.error("Download failed after all retries", extra={"url": url})
        return None

    # Schema Validation

    def _validate_article(self, article: dict) -> bool:
        """ Validate Fields """
        for field in self.REQUIRED_FIELDS:
            value = article.get(field)
            if not value or (isinstance(value, str) and len(value.strip()) == 0):
                self.logger.warning(
                    "Invalid article: required field missing",
                    extra={"url": article.get("url"), "missing_field": field}
                )
                return False

        return True

    # Utility Methods

    @staticmethod
    def _generate_article_id(url: str) -> str:
        """ Generate ID """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def clean_text(text: str) -> str:
        """ Clean Text """
        if not text:
            return ""
        # Normalize Whitespace
        lines = text.strip().splitlines()
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(cleaned_lines)

    def make_absolute_url(self, relative_url: str) -> str:
        """ Absolute URL """
        if relative_url.startswith("http"):
            return relative_url
        # Join URL
        base = self.base_url.rstrip("/")
        path = relative_url.lstrip("/")
        return f"{base}/{path}"
