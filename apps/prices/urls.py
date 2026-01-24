"""
URL configuration for prices app.
"""

from django.urls import path
from . import views

app_name = 'prices'

urlpatterns = [
    path(
        'all/',
        views.AllPricesAPIView.as_view(),
        name='all-prices'
    ),
    path(
        'latest/',
        views.LatestPriceAPIView.as_view(),
        name='latest-price'
    ),
    path(
        'range/',
        views.PricesByDateRangeAPIView.as_view(),
        name='prices-by-range'
    ),
]
