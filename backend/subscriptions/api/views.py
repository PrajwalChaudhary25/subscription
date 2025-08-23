from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from ..models import UserSubscription, SubscriptionPlan, Payment
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer, UserSerializer, PaymentSerializer
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
import logging

# Set up logging
logger = logging.getLogger(__name__)

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
        subscriptions = UserSubscription.objects.filter(user__id=user_id).order_by('-start_date')
        serializer = UserSubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
    

class RenewSubscriptionView(generics.GenericAPIView):
    # authentication_classes = [TokenAuthentication]
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
    # authentication_classes = [TokenAuthentication]

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
            active_subscriptions = UserSubscription.objects.filter(user=user,end_date__gte=timezone.now().date())
            if active_subscriptions.exists():
                return Response(
                    {"error": "You already have an active subscription."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pending_payment = Payment.objects.filter(user=user, is_verified=False).first()
            if pending_payment:
                return Response(
                    {"error": "You have a pending payment awaiting verification."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            plan = get_object_or_404(SubscriptionPlan, pk=plan_id)
            
            return Response(
                {"message": "Plan selected. Please upload payment proof.", "plan_id": plan.id},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class UserDetailView(generics.RetrieveAPIView):
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            print(f"Error in UserDetailView: {str(e)}")
            return Response(
                {"error": "Failed to fetch user data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentCreateView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    def create(self, request, *args, **kwargs):
        
        # Check for required fields
        if 'payment_proof' not in request.FILES:
            return Response(
                {"error": "Payment proof file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'plan' not in request.data:
            logger.error("PaymentCreateView - Missing 'plan' in request.data")
            return Response(
                {"error": "Plan ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already has a pending payment
        existing_pending = Payment.objects.filter(user=request.user, is_verified=False).first()
        if existing_pending:
            logger.error(f"PaymentCreateView - User already has pending payment")
            return Response(
                {"error": "You already have a pending payment awaiting verification"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has an active subscription
        active_sub = UserSubscription.objects.filter(user=request.user, end_date__gte=timezone.now().date()).first()
        if active_sub:
            logger.error(f"PaymentCreateView - User already has active subscription")
            return Response(
                {"error": "You already have an active subscription"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate plan ID
        try:
            plan_id = request.data.get('plan')
            logger.info(f"PaymentCreateView - Plan ID: {plan_id}")
            
            # Check if plan exists
            plan = SubscriptionPlan.objects.get(id=plan_id)
            logger.info(f"PaymentCreateView - Found plan: {plan}")
                
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"PaymentCreateView - Plan not found: {plan_id}")
            return Response(
                {"error": "Plan not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"PaymentCreateView - Error validating plan: {str(e)}")
            return Response(
                {"error": f"Error validating plan: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Proceed with the default create method
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"PaymentCreateView - Success: {response.data}")
            return response
        except Exception as e:
            logger.error(f"PaymentCreateView - Error during creation: {str(e)}")
            return Response(
                {"error": f"Failed to create payment: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        logger.info(f"PaymentCreateView.perform_create - Validated data: {serializer.validated_data}")
        
        # Add the user to the payment
        serializer.save(user=self.request.user)
        logger.info("PaymentCreateView.perform_create - Payment saved successfully")