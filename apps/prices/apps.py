"""
Application configuration for prices app.
"""

from django.apps import AppConfig


class PricesConfig(AppConfig):
    """Configuration class for prices app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.prices'
    verbose_name = 'Price Tracker'
    
    def ready(self):
        """Initialize app when Django starts."""
        import apps.prices.signals  # noqa
