from rest_framework import serializers
from ..models import SubscriptionPlan, UserSubscription, Payment
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all(), write_only=True, source='plan')
    is_active = serializers.ReadOnlyField()
    class Meta:
        model = UserSubscription
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    plan = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all(), required=True)
    subscription = serializers.PrimaryKeyRelatedField(read_only=True) 
    
    class Meta:
        model = Payment
        fields = ['id', 'plan', 'subscription', 'payment_proof', 'is_verified', 'created_at', 'user']
        read_only_fields = ['is_verified', 'user', 'created_at', 'subscription']  # user is set automatically from request

