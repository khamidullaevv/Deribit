"""
REST API views for price data.
"""

import logging
from datetime import datetime

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import PriceTickerChoices
from .serializers import (
    PriceSerializer,
    TickerFilterSerializer,
    DateRangeFilterSerializer,
)
from .services import PriceService

logger = logging.getLogger(__name__)


class BaseTickerAPIView(APIView):
    """
    Base class for API views that require ticker validation.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_service = PriceService()
    
    def _validate_ticker(self, request) -> str:
        """
        Validate and extract ticker from query parameters.
        
        Args:
            request: HTTP request object
            
        Returns:
            Validated ticker string
            
        Raises:
            ValidationError: If ticker is missing or invalid
        """
        serializer = TickerFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            raise ValidationError(
                detail=serializer.errors,
                code='invalid_ticker'
            )
        return serializer.validated_data['ticker']


class AllPricesAPIView(BaseTickerAPIView):
    """
    API endpoint to get all price records for a cryptocurrency ticker.
    
    GET /api/prices/all/?ticker=btc_usd
    
    Returns:
        - count: Total number of records
        - results: Array of price records ordered by timestamp (newest first)
    """
    
    def get(self, request):
        """
        Get all price records for a given ticker.
        
        Query Parameters:
            ticker (required): btc_usd or eth_usd
            
        Returns:
            200: List of price records
            400: Invalid ticker
        """
        try:
            ticker = self._validate_ticker(request)
        except ValidationError as e:
            return Response(
                {
                    'error': 'Invalid ticker parameter',
                    'details': e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get prices from service
        queryset = self.price_service.get_all_prices(ticker)
        
        # Apply pagination if needed
        page = request.query_params.get('page', 1)
        per_page = request.query_params.get('per_page', 100)
        
        try:
            page = int(page)
            per_page = min(int(per_page), 1000)  # Max 1000 per page
        except ValueError:
            return Response(
                {
                    'error': 'Invalid pagination parameters',
                    'details': {'page': 'Must be integer', 'per_page': 'Must be integer'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_idx = (page - 1) * per_page
        paginated_queryset = queryset[start_idx:start_idx + per_page]
        
        serializer = PriceSerializer(paginated_queryset, many=True)
        
        return Response(
            {
                'count': queryset.count(),
                'ticker': ticker,
                'page': page,
                'per_page': per_page,
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )


class LatestPriceAPIView(BaseTickerAPIView):
    """
    API endpoint to get the latest price for a cryptocurrency ticker.
    
    GET /api/prices/latest/?ticker=btc_usd
    
    Returns:
        - ticker: The ticker symbol
        - price: The latest price value
        - timestamp: Unix timestamp of the price
        - created_at: When the record was created
    """
    
    def get(self, request):
        """
        Get the most recent price for a given ticker.
        
        Query Parameters:
            ticker (required): btc_usd or eth_usd
            
        Returns:
            200: Latest price record
            400: Invalid ticker
            404: No price records found for ticker
        """
        try:
            ticker = self._validate_ticker(request)
        except ValidationError as e:
            return Response(
                {
                    'error': 'Invalid ticker parameter',
                    'details': e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get latest price
        latest_price = self.price_service.get_latest_price(ticker)
        
        if not latest_price:
            return Response(
                {
                    'error': f'No price records found for {ticker}',
                    'ticker': ticker
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PriceSerializer(latest_price)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class PricesByDateRangeAPIView(BaseTickerAPIView):
    """
    API endpoint to get prices for a date range.
    
    GET /api/prices/range/?ticker=btc_usd&start_date=2024-01-01T00:00:00&end_date=2024-01-02T00:00:00
    
    Returns:
        - count: Total number of records in range
        - results: Array of price records within the date range
    """
    
    def get(self, request):
        """
        Get prices within a date range for a given ticker.
        
        Query Parameters:
            ticker (required): btc_usd or eth_usd
            start_date (required): Start datetime (ISO 8601 format)
            end_date (required): End datetime (ISO 8601 format)
            
        Returns:
            200: Price records in the range
            400: Invalid parameters
        """
        # Validate date range parameters
        serializer = DateRangeFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid parameters',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        ticker = validated_data['ticker']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']
        
        # Get prices in range
        queryset = self.price_service.get_prices_by_datetime_range(
            ticker,
            start_date,
            end_date
        )
        
        # Apply pagination
        page = request.query_params.get('page', 1)
        per_page = request.query_params.get('per_page', 100)
        
        try:
            page = int(page)
            per_page = min(int(per_page), 1000)
        except ValueError:
            return Response(
                {
                    'error': 'Invalid pagination parameters',
                    'details': {'page': 'Must be integer', 'per_page': 'Must be integer'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_idx = (page - 1) * per_page
        paginated_queryset = queryset[start_idx:start_idx + per_page]
        
        price_serializer = PriceSerializer(paginated_queryset, many=True)
        
        return Response(
            {
                'count': queryset.count(),
                'ticker': ticker,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'page': page,
                'per_page': per_page,
                'results': price_serializer.data
            },
            status=status.HTTP_200_OK
        )
