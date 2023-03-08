from django import forms
from .models import Driver, CustomUser, Car, Customer
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class RegistrationForm(UserCreationForm):
    CHOICES = [('customer', 'Customer'), ('driver', 'Driver')]
    user_type = forms.ChoiceField(choices=CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'user_type']


User = get_user_model()

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email')

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['address', 'phone']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.update(CustomUserForm(instance=self.instance.user).fields)

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['make', 'model', 'year']
        widgets = {
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'})
        }

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['is_available', 'latitude', 'longitude']
        widgets = {
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = []
        widgets = {}

class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = []
        widgets = {}
