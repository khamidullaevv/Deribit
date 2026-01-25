

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_service = PriceService()
    
    def _validate_ticker(self, request) -> str:
        serializer = TickerFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            raise ValidationError(
                detail=serializer.errors,
                code='invalid_ticker'
            )
        return serializer.validated_data['ticker']


class AllPricesAPIView(BaseTickerAPIView):
    
    def get(self, request):
       
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
        
        queryset = self.price_service.get_all_prices(ticker)
        
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
    
    
    def get(self, request):
       
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
   
    def get(self, request):
      
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
        
        queryset = self.price_service.get_prices_by_datetime_range(
            ticker,
            start_date,
            end_date
        )
        
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
