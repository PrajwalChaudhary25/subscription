from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserSubscription, SubscriptionPlan
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework.authentication import TokenAuthentication



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
        current_date = timezone.now().date()
        if UserSubscription.objects.filter(user=user, end_date__gte=current_date).exists():
            raise ValidationError("You already have an active subscription.")
        serializer.save()

class UserSubscriptionRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    
class UserSubscriptions(APIView):
    def get(self, request, user_id):
        # Filter subscriptions where end_date is in the future
        current_date = timezone.now().date()
        active_subscriptions = UserSubscription.objects.filter(
            user__id=user_id,
            end_date__gte=current_date
        )
        serializer = UserSubscriptionSerializer(active_subscriptions, many=True)
        return Response(serializer.data)
    

class RenewSubscriptionView(generics.GenericAPIView):
    authentication_classes = [TokenAuthentication] # <-- ADDED THIS LINE
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Find the user's latest expired subscription to get the plan
        latest_expired_sub = UserSubscription.objects.filter(user=user).order_by('-end_date').first()

        if not latest_expired_sub:
            return Response(
                {"error": "No expired subscription found for this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # We assume payment is successful when this endpoint is hit
        new_subscription = UserSubscription(
            user=user,
            plan=latest_expired_sub.plan,
            start_date=timezone.now().date(),
        )
        new_subscription.save()

        return Response(
            {"message": "Subscription renewed successfully!"},
            status=status.HTTP_201_CREATED
        )


class PurchaseSubscriptionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication] # <-- ADDED THIS LINE

    def post(self, request, *args, **kwargs):
        user = request.user
        plan_id = request.data.get('plan_id')

        if not plan_id:
            return Response(
                {"error": "Please provide a 'plan_id' to purchase a subscription."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if the user already has an active subscription
            current_date = timezone.now().date()
            if UserSubscription.objects.filter(user=user, end_date__gte=current_date).exists():
                return Response(
                    {"error": "You already have an active subscription."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Retrieve the plan the user wants to purchase
            plan = get_object_or_404(SubscriptionPlan, pk=plan_id)

            # Create the new subscription for the user
            new_subscription = UserSubscription(
                user=user,
                plan=plan,
                start_date=timezone.now().date(),
            )
            new_subscription.save()

            return Response(
                {"message": f"Subscription to {plan.name} successful!"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class UserDetailView(generics.RetrieveAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in UserDetailView: {str(e)}")  # Debug print
            return Response(
                {"error": "Failed to fetch user data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
