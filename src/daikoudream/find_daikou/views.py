from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from find_daikou.models import Driver, Order
from .forms import DriverForm, RegistrationForm
from .models import CustomUser, Driver, Customer


def available_drivers(request):
    drivers = Driver.objects.filter(is_available=True)
    driver_points = [{'type': 'Feature',
                      'geometry': {'type': 'Point', 'coordinates': [d.longitude, d.latitude]},
                      'properties': {'name': d.user.username}} for d in drivers]

    data = {
        'type': 'FeatureCollection',
        'features': driver_points
    }

    return JsonResponse(data)


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data.get('user_type')
            user = form.save()
            if user_type == 'customer':
                Customer.objects.create(user=user)
            elif user_type == 'driver':
                Driver.objects.create(user=user)
            return redirect('index')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def index(request):
    """ A view responsible for welcoming users. """
    # Determine user type
    is_customer = False
    is_driver = False

    if request.user.is_authenticated:
        if hasattr(request.user, 'customer'):
            is_customer = True
        elif hasattr(request.user, 'driver'):
            is_driver = True

        # Set button labels and URLs
        if is_customer:
            call_driver_url = '/call_driver'
            call_driver_label = 'Call driver'
            if request.user.customer.orders.filter(completed=False).exists():
                call_driver_url = '/cancel_driver'
                call_driver_label = 'Cancel driver'
            buttons = [
                {'url': call_driver_url, 'label': call_driver_label},
                {'url': '/history', 'label': 'See history'},
                {'url': '/update_info', 'label': 'Update information'},
            ]
        elif is_driver:
            start_driving_url = '/start_driving'
            start_driving_label = 'Start driving'
            if request.user.driver.is_available:
                start_driving_url = '/stop_driving'
                start_driving_label = 'Stop driving'
            buttons = [
                {'url': start_driving_url, 'label': start_driving_label},
                {'url': '/history', 'label': 'See history'},
                {'url': '/update_info', 'label': 'Update information'},
            ]
        else:
            buttons = [
                {'url': '/logout', 'label': 'Logout'},
            ]
    else:
        buttons = [
            {'url': '/login', 'label': 'Log in'},
            {'url': '/register', 'label': 'Register'},
        ]
    return render(request, 'active_drivers.html', {"buttons": buttons})
