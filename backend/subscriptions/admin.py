from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, Payment
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_months')
    search_fields = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'status_icon', 'start_date', 'end_date')
    readonly_fields = ('status',)
    list_filter = ('plan', 'status')
    search_fields = ('user__username', 'plan__name')
    
    def status_icon(self, obj):
        """Display visual status indicator with tick/cross marks"""
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span> <span style="color: green;">Active</span>')
        else:
            # Status is ACTIVE but date has expired
            return format_html('<span style="color: red; font-size: 18px;">X </span> <span style="color: orange;"></span>')
     
    status_icon.short_description = 'Status'
    
    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return (
                (None, {
                    'fields': ('user', 'plan', 'status', 'start_date', 'end_date')
                }),
            )
        else:
            return (
                (None, {
                    'fields': ('user', 'plan', 'status'),
                    'readonly_fields': ('start_date', 'end_date')
                }),
            )

    def save_model(self, request, obj, form, change):
        # If status is ACTIVE and dates aren't set, set them
        if obj.status == 'ACTIVE' and not obj.start_date:
            obj.start_date = timezone.now().date()
        # end_date will be calculated automatically in the model's save method
        super().save_model(request, obj, form, change)



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_verified', 'created_at', 'payment_proof_display', 'subscription_status')
    list_filter = ('is_verified', 'plan')
    search_fields = ('user__username', 'plan__name')
    readonly_fields = ('payment_proof_display', 'user', 'plan', 'subscription', 'created_at')
    fields = ('user', 'plan', 'payment_proof_display', 'is_verified', 'subscription', 'created_at')

    def payment_proof_display(self, obj):
        if obj.payment_proof:
            return format_html('<a href="{}" target="_blank">View Payment Proof</a>', obj.payment_proof.url)
        return "No image"

    payment_proof_display.short_description = 'Payment Proof Link'
    
    def subscription_status(self, obj):
        if obj.subscription:
            return format_html('<span style="color: green;">✓ Created</span>')
        elif obj.is_verified:
            return format_html('<span style="color: orange;">⚠ Verified but no subscription</span>')
        
    subscription_status.short_description = 'Subscription'
    
    def save_model(self, request, obj, form, change):
        # Check if is_verified changed from False to True
        if change and obj.is_verified:
            old_obj = Payment.objects.get(pk=obj.pk)
            if not old_obj.is_verified and not obj.subscription and obj.plan:
                # Create a new UserSubscription when payment is verified
                new_subscription = UserSubscription(
                    user=obj.user,
                    plan=obj.plan,
                    start_date=timezone.now().date()
                )
                # end_date will be calculated automatically in the model's save method
                new_subscription.save()
                
                # Link the subscription to this payment
                obj.subscription = new_subscription
                
                messages.success(request, f"Subscription for {obj.user.username} has been created and activated.")
        
        super().save_model(request, obj, form, change)

