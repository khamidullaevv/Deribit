"""
Price models for Deribit price tracker.
"""

from django.db import models
from django.core.validators import MinValueValidator


class PriceTickerChoices(models.TextChoices):
    """Available cryptocurrency tickers."""
    BTC_USD = 'btc_usd', 'Bitcoin USD'
    ETH_USD = 'eth_usd', 'Ethereum USD'


class Price(models.Model):
    """
    Model to store historical price data from Deribit.
    
    Attributes:
        ticker: The cryptocurrency ticker (btc_usd or eth_usd)
        price: The price value in USD
        timestamp: Unix timestamp of the price
        created_at: When this record was created in the database
    """
    
    ticker = models.CharField(
        max_length=20,
        choices=PriceTickerChoices.choices,
        db_index=True
    )
    price = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    timestamp = models.BigIntegerField(
        db_index=True,
        help_text="Unix timestamp (seconds)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prices'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ticker', 'timestamp']),
            models.Index(fields=['ticker', '-timestamp']),
        ]
        verbose_name = 'Price'
        verbose_name_plural = 'Prices'

    def __str__(self):
        return f"{self.ticker}: ${self.price} at {self.timestamp}"

    def __repr__(self):
        return (
            f"Price(ticker={self.ticker!r}, price={self.price}, "
            f"timestamp={self.timestamp}, id={self.id})"
        )
