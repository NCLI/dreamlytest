from django import forms
from .models import Driver, CustomUser
from django.contrib.auth.forms import UserCreationForm

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['latitude', 'longitude', 'license_number', 'bank_account_info', 'is_available']

class RegistrationForm(UserCreationForm):
    CHOICES = [('customer', 'Customer'), ('driver', 'Driver')]
    user_type = forms.ChoiceField(choices=CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'user_type']
