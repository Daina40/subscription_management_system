from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
import requests
from decouple import config
from django.shortcuts import render
from django.contrib.auth.models import User


from .models import Plan, Subscription, ExchangeRateLog
from .serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    CreateSubscriptionSerializer,
    ExchangeRateLogSerializer,
)

# Subscribe to a plan
class SubscribeView(generics.CreateAPIView):
    serializer_class = CreateSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        plan = serializer.validated_data['plan']
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=plan.duration_days)
        serializer.save(
            user=self.request.user,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        subscription = Subscription.objects.get(id=serializer.instance.id)
        output_serializer = SubscriptionSerializer(subscription)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

# List all subscriptions of the logged-in user
class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

# Cancel a subscription
class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        subscription_id = request.data.get('subscription_id')
        if not subscription_id:
            return Response({"error": "subscription_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            subscription = Subscription.objects.get(id=subscription_id, user=request.user)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)
        subscription.status = 'cancelled'
        subscription.save()
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)

# Fetch latest exchange rate using external API
class ExchangeRateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        base = request.query_params.get('base', 'USD')
        target = request.query_params.get('target', 'BDT')
        API_KEY = config('EXCHANGE_API_KEY')

        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{base}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            rate = data['conversion_rates'].get(target)

            if rate is None:
                return Response({"error": f"Conversion rate not found for {target}"}, status=status.HTTP_404_NOT_FOUND)

            # Save to ExchangeRateLog
            ExchangeRateLog.objects.create(
                base_currency=base,
                target_currency=target,
                rate=rate
            )

            return Response({
                "base_currency": base,
                "target_currency": target,
                "rate": rate,
                "fetched_at": timezone.now()
            })

        except requests.RequestException as e:
            return Response({"error": f"Error fetching exchange rate: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

def subscriptions_list(request):
    # Fetch all subscriptions with related user and plan
    subscriptions = Subscription.objects.select_related('user', 'plan').all()
    return render(request, 'subscriptions.html', {'subscriptions': subscriptions})
