from celery import shared_task
import requests
from .models import ExchangeRateLog

API_KEY = 'db0551c2f03c6f38c53c7087'

@shared_task
def fetch_usd_to_bdt_rate():
    url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            rate = data['conversion_rates'].get('BDT')
            if rate:
                ExchangeRateLog.objects.create(
                    base_currency='USD',
                    target_currency='BDT',
                    rate=rate
                )
        else:
            print(f"ExchangeRate API error: {response.status_code}")
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
