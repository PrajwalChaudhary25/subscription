from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription
from django.contrib.auth.models import User

# This serializer is correct as is. It serializes the user details.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active')

# This serializer is correct. We'll use it as a nested serializer below.
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'price', 'duration_months', 'active')

# --- This is the corrected serializer ---
class UserSubscriptionSerializer(serializers.ModelSerializer):
    # Use nested serializers to display the full object data instead of just the ID.
    # Setting read_only=True prevents the frontend from trying to change these fields.
    plan = SubscriptionPlanSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    # You must explicitly define model properties like `is_active`
    # so they are included in the serialized output.
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = ['user', 'plan', 'start_date', 'end_date', 'is_active']
        read_only_fields = ['start_date', 'end_date', 'is_active'] # Mark these as read-only

