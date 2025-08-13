from django.urls import path
from .views import (
    SubscriptionPlanListCreate,
    SubscriptionPlanRetrieveUpdateDestroy,
    UserSubscriptionListCreate, 
    UserSubscriptionRetrieveUpdateDestroy,  
    UserSubscriptions
)

urlpatterns = [
    path('plans/', SubscriptionPlanListCreate.as_view(), name='plan-list-create'),
    path('plans/<int:pk>/', SubscriptionPlanRetrieveUpdateDestroy.as_view(), name='plan-retrieve-update-destroy'),
    path('subscriptions/', UserSubscriptionListCreate.as_view(), name='subscription-list-create'), 
    path('subscriptions/<int:pk>/', UserSubscriptionRetrieveUpdateDestroy.as_view(), name='subscription-retrieve-update-destroy'), 
    path('users/<int:user_id>/subscriptions/', UserSubscriptions.as_view(), name='user-subscriptions'),
]

