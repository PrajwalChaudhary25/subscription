from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import UserSubscription
import random

def process_payment(user, plan):
    """
    Simulates a payment attempt by randomly returning True or False.
    """
    print(f"Attempting to process payment for user {user.username} for plan {plan.name}...")
    return random.random() < 0.8

class Command(BaseCommand):
    help = 'Renews active subscriptions that have reached their end date and have a successful payment.'

    def handle(self, *args, **options):
        expired_subscriptions = UserSubscription.objects.filter(
            is_active=True,
            end_date__lte=timezone.now().date()
        )

        self.stdout.write(self.style.NOTICE(f'Found {expired_subscriptions.count()} expired subscriptions to process.'))

        for subscription in expired_subscriptions:
            payment_successful = process_payment(subscription.user, subscription.plan)

            if payment_successful:
                # Deactivate the old subscription
                subscription.is_active = False
                subscription.save()

                # Create a new subscription instance.
                # Crucially, we now explicitly set the start_date to the current date.
                new_subscription = UserSubscription(
                    user=subscription.user,
                    plan=subscription.plan,
                    start_date=timezone.now().date(),
                )
                
                # Call the save method to trigger our end_date calculation
                new_subscription.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully renewed subscription for user {subscription.user.username}.'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'Payment failed for user {subscription.user.username}. Subscription not renewed.'
                ))
        
        self.stdout.write(self.style.SUCCESS('Subscription renewal process completed.'))