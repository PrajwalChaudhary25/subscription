from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = ['user', 'plan', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['start_date']