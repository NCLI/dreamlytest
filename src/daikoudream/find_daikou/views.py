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
            buttons = [
                {'url': '/history', 'label': 'See history'},
                {'url': '/update_info', 'label': 'Update information'},
            ]
            if request.user.customer.orders.filter(completed=False).exists():
                buttons.append(
                    {
                        "url": '/cancel_driver',
                        "label": 'Cancel driver'
                    }
                )
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
    return render(request, 'active_drivers.html', {"buttons": buttons, "is_customer": is_customer})

def call_driver(request):
    if request.method == 'POST':
        # Get the pick-up time from the form data
        # pickup_time = request.POST.get('pickup_time')

        # Get the departure and arrival coordinates from hidden inputs
        departure = request.POST.get('departure')
        arrival = request.POST.get('arrival')

        # Print the received data
        # print(f"Pick-up time: {pickup_time}")
        print(f"Departure: {departure}")
        print(f"Arrival: {arrival}")

        # Return a response, e.g. a redirect to a success page
        return redirect('index')

    # If the request is not a POST request, render the template with the form
    return render(request, 'call_driver.html')
