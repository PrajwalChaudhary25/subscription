# subscriptions/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - Rs{self.price}"
    
class UserSubscription(models.Model):
    # Subscription status choices for admin verification and tracking
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELED', 'Canceled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'ACTIVE' and self.end_date and self.end_date >= timezone.now().date()

    def __str__(self):
        return f"{self.user.username}'s {self.plan.name} subscription ({self.status})"
    
    def save(self, *args, **kwargs):
        # Automatically calculate the end_date when start_date is set and end_date is not
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + relativedelta(months=self.plan.duration_months)
        super().save(*args, **kwargs)


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, null=True, blank=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        plan_name = self.plan.name if self.plan else "No Plan"
        return f"Payment for {self.user.username} - {plan_name} ({self.created_at.strftime('%Y-%m-%d')})"

