from django.contrib import admin
from .models import CustomUser, Customer, Car, Driver, Order

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'saved_payment_info')

class CarAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'year', 'customer')

class DriverAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_available', 'latitude', 'longitude', 'license_number', 'bank_account_info')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'driver', 'car', 'pickup_time', 'completed')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Car, CarAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(Order, OrderAdmin)
