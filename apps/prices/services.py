"""
Services layer for price management and Deribit API interaction.
"""

import logging
import time
from decimal import Decimal
from typing import Dict, Optional, Tuple

import requests
from django.conf import settings

from .models import Price, PriceTickerChoices

logger = logging.getLogger(__name__)


# =========================
# Deribit API client
# =========================
class DeribitAPIClient:
    """
    Synchronous client for Deribit REST API.
    Used inside Celery tasks (safe & simple).
    """

    DEFAULT_TICKERS = ("btc_usd", "eth_usd")

    def __init__(
        self,
        base_url: str = settings.DERIBIT_BASE_URL,
        timeout: int = settings.DERIBIT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_index_price(self, ticker: str) -> Optional[Decimal]:
        """
        Fetch index price for a single ticker from Deribit.

        Example:
        GET /public/get_index_price?index_name=btc_usd
        """
        url = f"{self.base_url}/public/get_index_price"
        params = {"index_name": ticker}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            result = data.get("result")

            if not result or "index_price" not in result:
                logger.warning(f"No price data returned for {ticker}")
                return None

            return Decimal(str(result["index_price"]))

        except requests.RequestException as exc:
            logger.error(f"Deribit request failed for {ticker}: {exc}")
            return None


# =========================
# Price business service
# =========================
class PriceService:
    """
    Business logic layer for prices.

    Responsibilities:
    - Fetch prices from Deribit
    - Save prices to DB
    - Query prices
    """

    def __init__(self, client: Optional[DeribitAPIClient] = None):
        self.client = client or DeribitAPIClient()

    # ---------- SAVE ----------
    def save_price(self, ticker: str, price: Decimal, timestamp: int) -> Price:
        """
        Save a single price record.
        """
        if ticker not in dict(PriceTickerChoices.choices):
            raise ValueError(f"Invalid ticker: {ticker}")

        return Price.objects.create(
            ticker=ticker,
            price=price,
            timestamp=timestamp,
        )

    def fetch_and_save_prices(
        self,
        tickers: Tuple[str, ...] = DeribitAPIClient.DEFAULT_TICKERS,
    ) -> Dict[str, Optional[Price]]:
        """
        Fetch prices from Deribit and save them to DB.
        Used by Celery beat (every minute).
        """
        results: Dict[str, Optional[Price]] = {}
        timestamp = int(time.time())

        for ticker in tickers:
            price = self.client.get_index_price(ticker)

            if price is None:
                logger.warning(f"Price not saved (no data): {ticker}")
                results[ticker] = None
                continue

            try:
                price_obj = self.save_price(
                    ticker=ticker,
                    price=price,
                    timestamp=timestamp,
                )
                results[ticker] = price_obj
                logger.info(f"Saved {ticker}: {price}")
            except Exception as exc:
                logger.error(f"Failed to save {ticker}: {exc}")
                results[ticker] = None

        return results

    # ---------- READ ----------
    def get_all_prices(self, ticker: str):
        return Price.objects.filter(
            ticker=ticker
        ).order_by("-timestamp")

    def get_latest_price(self, ticker: str) -> Optional[Price]:
        return (
            Price.objects.filter(ticker=ticker)
            .order_by("-timestamp")
            .first()
        )

    def get_prices_by_timestamp_range(
        self,
        ticker: str,
        start_ts: int,
        end_ts: int,
    ):
        return Price.objects.filter(
            ticker=ticker,
            timestamp__gte=start_ts,
            timestamp__lte=end_ts,
        ).order_by("-timestamp")
    def get_price_at_timestamp(
        self,
        ticker: str,
        timestamp: int,
    ) -> Optional[Price]:
        return Price.objects.filter(
            ticker=ticker,
            timestamp=timestamp,
        ).first()