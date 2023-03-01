from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point

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

def open_orders(request):
    # Retrieve all open orders from the database
    orders = Order.objects.filter(driver=None)

    # Create a list of features for the OpenLayers map
    features = []
    for order in orders:
        # Create a point feature for the pickup location
        pickup_location = Point(order.pickup_longitude, order.pickup_latitude)
        pickup_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [pickup_location.x, pickup_location.y]
            },
            'properties': {
                'id': order.id,
                'type': 'pickup',
                'description': "Nada"
            }
        }
        features.append(pickup_feature)

        # Create a point feature for the dropoff location
        dropoff_location = Point(order.dropoff_longitude, order.dropoff_latitude)
        dropoff_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [dropoff_location.x, dropoff_location.y]
            },
            'properties': {
                'id': order.id,
                'type': 'dropoff',
                'description': "Nada"
            }
        }
        features.append(dropoff_feature)

    context = {
        'orders': orders,
        'features': features
    }

    return render(request, 'open_orders.html', context)

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
    has_active_order = False
    orders = None
    features = None

    if request.user.is_authenticated:
        if hasattr(request.user, 'customer'):
            is_customer = True
        elif hasattr(request.user, 'driver'):
            is_driver = True

        # Set button labels and URLs
        if is_customer:
            buttons = [
                {'url': '/dashboard/history', 'label': 'See history'},
                {'url': '/update_info', 'label': 'Update information'},
            ]
            if request.user.customer.orders.filter(completed=False).exists():
                buttons.append(
                    {
                        "url": '/cancel_driver',
                        "label": 'Cancel driver'
                    }
                )
                has_active_order = True
        elif is_driver:
            start_driving_url = '/start_driving'
            start_driving_label = 'Start driving'
            if request.user.driver.is_available:
                start_driving_url = '/stop_driving'
                start_driving_label = 'Stop driving'
            buttons = [
                {'url': start_driving_url, 'label': start_driving_label},
                {'url': '/dashboard/history', 'label': 'See history'},
                {'url': '/update_info', 'label': 'Update information'},
            ]
            # Retrieve all open orders from the database
            orders = Order.objects.filter(driver=None)

            # Create a list of features for the OpenLayers map
            features = []
            for order in orders:
                # Create a point feature for the pickup location
                pickup_location = Point(order.pickup_longitude, order.pickup_latitude)
                pickup_feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [pickup_location.x, pickup_location.y]
                    },
                    'properties': {
                        'id': order.id,
                        'type': 'pickup',
                        'description': "Nada"
                    }
                }
                features.append(pickup_feature)

                # Create a point feature for the dropoff location
                dropoff_location = Point(order.dropoff_longitude, order.dropoff_latitude)
                dropoff_feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [dropoff_location.x, dropoff_location.y]
                    },
                    'properties': {
                        'id': order.id,
                        'type': 'dropoff',
                        'description': "Nada"
                    }
                }
                features.append(dropoff_feature)

        else:
            buttons = [
                {'url': '/logout', 'label': 'Logout'},
            ]
    else:
        buttons = [
            {'url': '/login', 'label': 'Log in'},
            {'url': '/register', 'label': 'Register'},
        ]
    return render(request, 'active_drivers.html', {"buttons": buttons,
                                                   "is_customer": is_customer,
                                                   "has_active_order": has_active_order,
                                                   "is_driver": is_driver,
                                                   "orders": orders,
                                                   "features": features
                                                   })

def call_driver(request):
    # Get the pick-up time from the form data
    print(request)
    pickup_time = request.GET.get('time')

    # Get the departure and arrival coordinates from hidden inputs
    departure = request.GET.get('departure')
    arrival = request.GET.get('arrival')

    # Print the received data
    print(f"Pick-up time: {pickup_time}")
    print(f"Departure: {departure}")
    print(f"Arrival: {arrival}")

    # Return a response, e.g. a redirect to a success page
    return redirect('index')


@login_required
def history(request):
    user = request.user
    if hasattr(request.user, 'customer'):
        orders = Order.objects.filter(customer=user.customer)
    elif hasattr(request.user, 'driver'):
        orders = Order.objects.filter(driver=user.driver)
    else:
        # If the user is not a Customer or a Driver, return an error message
        return render(request, 'error.html', {'error': 'You must be a Customer or a Driver to view previous orders.'})

    order_info = []
    for order in orders:
        info = {
            'start_location': f"{order.pickup_latitude}, {order.pickup_longitude}",
            'end_location': f"{order.dropoff_latitude}, {order.dropoff_longitude}",
            'car_make': order.car.make,
            'car_model': order.car.model,
            'car_year': order.car.year,
            'order_completed': order.completed,
        }
        order_info.append(info)

    context = {
        'orders': order_info,
    }

    return render(request, 'history.html', context)
