from django.urls import path
from .views import (
    SubscriptionPlanListCreate,
    SubscriptionPlanRetrieveUpdateDestroy,
    UserSubscriptionListCreate, 
    UserSubscriptionRetrieveUpdateDestroy,  
    UserSubscriptions, 
    RenewSubscriptionView,
    PurchaseSubscriptionView,
    UserDetailView,
)

urlpatterns = [
    path('plans/', SubscriptionPlanListCreate.as_view(), name='plan-list-create'),
    path('plans/<int:pk>/', SubscriptionPlanRetrieveUpdateDestroy.as_view(), name='plan-retrieve-update-destroy'),
    path('subscriptions/', UserSubscriptionListCreate.as_view(), name='subscription-list-create'), 
    path('subscriptions/<int:pk>/', UserSubscriptionRetrieveUpdateDestroy.as_view(), name='subscription-retrieve-update-destroy'), 
    path('users/<int:user_id>/subscriptions/', UserSubscriptions.as_view(), name='user-subscriptions'),
    path('renew/', RenewSubscriptionView.as_view(), name='renew-subscription'),
    path('purchase/', PurchaseSubscriptionView.as_view(), name='purchase-subscription'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
]