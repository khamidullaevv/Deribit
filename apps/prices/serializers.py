"""
Serializers for Price API endpoints.
"""

from rest_framework import serializers
from .models import Price, PriceTickerChoices


class PriceSerializer(serializers.ModelSerializer):
    """
    Serializer for Price model.
    
    Provides clean, typed responses for API endpoints.
    """
    
    ticker_display = serializers.CharField(
        source='get_ticker_display',
        read_only=True
    )
    
    class Meta:
        model = Price
        fields = [
            'id',
            'ticker',
            'ticker_display',
            'price',
            'timestamp',
            'created_at',
        ]
        read_only_fields = fields
    
    def to_representation(self, instance):
        """
        Override to provide consistent decimal representation.
        """
        data = super().to_representation(instance)
        data['price'] = str(instance.price)
        return data


class TickerFilterSerializer(serializers.Serializer):
    """
    Serializer for validating ticker query parameter.
    """
    
    ticker = serializers.ChoiceField(
        choices=PriceTickerChoices.choices,
        required=True,
        help_text="Cryptocurrency ticker: btc_usd or eth_usd"
    )


class DateRangeFilterSerializer(serializers.Serializer):
    """
    Serializer for validating date range query parameters.
    """
    
    ticker = serializers.ChoiceField(
        choices=PriceTickerChoices.choices,
        required=True
    )
    start_date = serializers.DateTimeField(
        required=True,
        help_text="Start datetime (ISO 8601 format)"
    )
    end_date = serializers.DateTimeField(
        required=True,
        help_text="End datetime (ISO 8601 format)"
    )
    
    def validate(self, data):
        """
        Validate that end_date is after start_date.
        """
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                "end_date must be after start_date"
            )
        return data


class PriceListResponseSerializer(serializers.Serializer):
    """
    Serializer for list response format.
    """
    
    count = serializers.IntegerField()
    results = PriceSerializer(many=True)


class PriceDetailResponseSerializer(serializers.Serializer):
    """
    Serializer for single price detail response.
    """
    
    ticker = serializers.CharField()
    price = serializers.DecimalField(max_digits=20, decimal_places=2)
    timestamp = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for error response format.
    """
    
    error = serializers.CharField()
    details = serializers.JSONField(required=False)
