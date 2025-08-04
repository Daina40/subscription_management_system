from django.urls import path
from .views import (
    SubscribeView,
    SubscriptionListView,
    CancelSubscriptionView,
    ExchangeRateView,
)

urlpatterns = [
    path('api/subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('api/subscriptions/', SubscriptionListView.as_view(), name='subscriptions'),
    path('api/cancel/', CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('api/exchange-rate/', ExchangeRateView.as_view(), name='exchange_rate'),
]
