"""
Celery tasks for price fetching and management.
"""

import asyncio
import logging

from celery import shared_task
from django.utils import timezone

from .services import PriceService

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=300,
)
def fetch_deribit_prices(self):
    try:
        price_service = PriceService()
        
        # <- Здесь убираем asyncio.run
        result = price_service.fetch_and_save_prices()
        
        successful = sum(1 for v in result.values() if v is not None)
        failed = sum(1 for v in result.values() if v is None)
        
        logger.info(
            f"Fetch complete: {successful} successful, {failed} failed. "
            f"Timestamp: {timezone.now().isoformat()}"
        )
        
        return {
            'status': 'success',
            'successful': successful,
            'failed': failed,
            'timestamp': timezone.now().isoformat(),
            'results': {
                ticker: (
                    {
                        'price': str(price.price),
                        'timestamp': price.timestamp,
                        'id': price.id
                    } if price else None
                )
                for ticker, price in result.items()
            }
        }
    
    except Exception as exc:
        logger.error(
            f"Error fetching prices (attempt {self.request.retries}): {str(exc)}",
            exc_info=True
        )
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(
    bind=True,
    time_limit=60,
)
def cleanup_old_prices(self, days_to_keep: int = 90):
    """
    Periodic task to delete old price records.
    
    Keeps only recent data to manage database size.
    
    Args:
        self: Task instance
        days_to_keep: Number of days of historical data to keep
        
    Returns:
        Dictionary with deletion count
    """
    try:
        from .models import Price
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        cutoff_timestamp = int(cutoff_date.timestamp())
        
        # Delete old records
        deleted_count, _ = Price.objects.filter(
            timestamp__lt=cutoff_timestamp
        ).delete()
        
        logger.info(
            f"Cleanup: Deleted {deleted_count} price records older than "
            f"{days_to_keep} days"
        )
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_timestamp': cutoff_timestamp,
        }
    
    except Exception as exc:
        logger.error(f"Error during cleanup: {str(exc)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(exc),
        }
