
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from django.test import TestCase, Client
from django.utils import timezone
from rest_framework import status

from .models import Price, PriceTickerChoices
from .services import PriceService, DeribitAPIClient


class PriceModelTestCase(TestCase):
    
    def setUp(self):
        self.price = Price.objects.create(
            ticker='btc_usd',
            price=Decimal('50000.00'),
            timestamp=1234567890
        )
    
    def test_price_creation(self):
        self.assertEqual(self.price.ticker, 'btc_usd')
        self.assertEqual(self.price.price, Decimal('50000.00'))
        self.assertEqual(self.price.timestamp, 1234567890)
    
    def test_price_string_representation(self):
        expected = "btc_usd: $50000.00 at 1234567890"
        self.assertEqual(str(self.price), expected)
    
    def test_invalid_negative_price(self):
        with self.assertRaises(Exception):
            Price.objects.create(
                ticker='btc_usd',
                price=Decimal('-100.00'),
                timestamp=1234567890
            )
    
    def test_price_ticker_choices(self):
        valid_tickers = ['btc_usd', 'eth_usd']
        for ticker in valid_tickers:
            price = Price.objects.create(
                ticker=ticker,
                price=Decimal('1000.00'),
                timestamp=1234567890
            )
            self.assertEqual(price.ticker, ticker)


class PriceServiceTestCase(TestCase):
    
    def setUp(self):
        self.service = PriceService()
        self.current_time = timezone.now()
        self.current_timestamp = int(self.current_time.timestamp())
    
    def test_save_price(self):
        price = self.service.save_price(
            ticker='btc_usd',
            price=Decimal('50000.00'),
            timestamp=self.current_timestamp
        )
        
        self.assertIsNotNone(price.id)
        self.assertEqual(price.ticker, 'btc_usd')
        self.assertEqual(price.price, Decimal('50000.00'))
    
    def test_save_price_invalid_ticker(self):
        with self.assertRaises(ValueError):
            self.service.save_price(
                ticker='invalid_ticker',
                price=Decimal('1000.00'),
                timestamp=self.current_timestamp
            )
    
    def test_get_all_prices(self):
        for i in range(5):
            Price.objects.create(
                ticker='btc_usd',
                price=Decimal('50000.00') + i,
                timestamp=self.current_timestamp + i
            )
        
        prices = self.service.get_all_prices('btc_usd')
        self.assertEqual(prices.count(), 5)
    
    def test_get_latest_price(self):
        for i in range(3):
            Price.objects.create(
                ticker='btc_usd',
                price=Decimal('50000.00') + i,
                timestamp=self.current_timestamp + i
            )
        
        latest = self.service.get_latest_price('btc_usd')
        self.assertEqual(latest.price, Decimal('50002.00'))
    
    def test_get_latest_price_empty(self):
        latest = self.service.get_latest_price('btc_usd')
        self.assertIsNone(latest)
    
    def test_get_prices_by_date_range(self):
        for i in range(10):
            Price.objects.create(
                ticker='btc_usd',
                price=Decimal('50000.00'),
                timestamp=self.current_timestamp + i
            )
        
        prices = self.service.get_prices_by_date_range(
            ticker='btc_usd',
            start_timestamp=self.current_timestamp + 2,
            end_timestamp=self.current_timestamp + 7
        )
        


class PriceAPITestCase(TestCase):
    """Tests for Price API views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.current_time = timezone.now()
        self.current_timestamp = int(self.current_time.timestamp())
        
        for i in range(5):
            Price.objects.create(
                ticker='btc_usd',
                price=Decimal('50000.00') + i,
                timestamp=self.current_timestamp + i
            )
        
        for i in range(3):
            Price.objects.create(
                ticker='eth_usd',
                price=Decimal('3000.00') + i,
                timestamp=self.current_timestamp + i
            )
    
    def test_all_prices_endpoint(self):
        response = self.client.get('/api/prices/all/?ticker=btc_usd')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 5)
        self.assertEqual(len(data['results']), 5)
        self.assertEqual(data['ticker'], 'btc_usd')
    
    def test_all_prices_missing_ticker(self):
        response = self.client.get('/api/prices/all/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
    
    def test_latest_price_endpoint(self):
        response = self.client.get('/api/prices/latest/?ticker=btc_usd')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['ticker'], 'btc_usd')
        self.assertEqual(data['price'], '50004.00')
    
    def test_latest_price_not_found(self):
        response = self.client.get('/api/prices/latest/?ticker=xrp_usd')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_date_range_endpoint(self):
        start_date = (self.current_time + timedelta(seconds=1)).isoformat()
        end_date = (self.current_time + timedelta(seconds=3)).isoformat()
        
        response = self.client.get(
            f'/api/prices/range/?ticker=btc_usd&start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 3)
    
    def test_date_range_invalid_dates(self):
        start_date = (self.current_time + timedelta(seconds=5)).isoformat()
        end_date = (self.current_time + timedelta(seconds=1)).isoformat()
        
        response = self.client.get(
            f'/api/prices/range/?ticker=btc_usd&start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@pytest.mark.asyncio
class TestDeribitAPIClient:
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        client = DeribitAPIClient()
        assert client.base_url is not None
        assert client.timeout is not None
