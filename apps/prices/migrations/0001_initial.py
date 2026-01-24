"""
Initial migration for Price model.
"""

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Price',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(choices=[('btc_usd', 'Bitcoin USD'), ('eth_usd', 'Ethereum USD')], db_index=True, max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=20, validators=[django.core.validators.MinValueValidator(0)])),
                ('timestamp', models.BigIntegerField(db_index=True, help_text='Unix timestamp (seconds)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Price',
                'verbose_name_plural': 'Prices',
                'db_table': 'prices',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='price',
            index=models.Index(fields=['ticker', 'timestamp'], name='prices_ticker_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='price',
            index=models.Index(fields=['ticker', '-timestamp'], name='prices_ticker__timestamp_idx'),
        ),
    ]
