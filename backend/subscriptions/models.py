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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    
    # This new @property method dynamically calculates if the subscription is active.
    # It checks if the current date is before or on the end_date.
    @property
    def is_active(self):
        return self.end_date is None or self.end_date >= timezone.now().date()

    def __str__(self):
        return f"{self.user.username}'s {self.plan.name} subscription"

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan and self.start_date:
            self.end_date = self.start_date + relativedelta(months=self.plan.duration_months)
        super().save(*args, **kwargs)