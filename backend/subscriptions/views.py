from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer


# Create your views here.
class SubscriptionPlanListCreate(generics.ListCreateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

class SubscriptionPlanRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    
class UserSubscriptionListCreate(generics.ListCreateAPIView):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer

    def perform_create(self, serializer):
        user = serializer.validated_data['user']
        if UserSubscription.objects.filter(user=user, is_active=True).exists():
            raise ValidationError("You already have an active subscription.")
        serializer.save()

class UserSubscriptionRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    
class UserSubscriptions(APIView):
    def get(self, request, user_id):
        active_subscriptions = UserSubscription.objects.filter(
            user__id=user_id,
            is_active=True
        )
        serializer = UserSubscriptionSerializer(active_subscriptions, many=True)
        return Response(serializer.data)