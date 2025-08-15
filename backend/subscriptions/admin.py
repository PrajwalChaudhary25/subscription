from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_months')
    search_fields = ('name',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'status')
    list_filter = ('plan',) 
    search_fields = ('user__username', 'plan__name')
    fields = ('user', 'plan', 'start_date', 'end_date')

    def status(self, obj):
        # This method returns the boolean value of the is_active property
        # The Django admin will automatically display this as a green checkmark or a red X
        return obj.is_active
    
    status.boolean = True # This tells the Django admin to show a checkmark or an X
    status.short_description = 'Is Active' # This sets the column header in the admin