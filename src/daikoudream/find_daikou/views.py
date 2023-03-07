from datetime import datetime
from time import strptime

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.db import transaction
from django.views.decorators.http import require_POST

from find_daikou.models import Driver, Order, Car
from .forms import DriverForm, RegistrationForm, CarForm, CustomerForm
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
                'description': "Point where you would like to go to."
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
                'description': "Point where you would like to be picked up."
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
    is_available = False
    orders = []
    features = []
    cars =[]

    if request.user.is_authenticated:
        if hasattr(request.user, 'customer'):
            is_customer = True
            cars = Car.objects.filter(customer=request.user.customer)
        elif hasattr(request.user, 'driver'):
            is_driver = True
            if request.user.driver.is_available:
                is_available = True

        # Set button labels and URLs
        if is_customer:
            buttons = [
                {'url': '/dashboard/history', 'label': 'See history'},
                {'url': '/dashboard/modify_user', 'label': 'Update information'},
                {'url': '/dashboard/add_car', 'label': 'Add car'},
            ]
            if request.user.customer.orders.filter(completed=False).exists():
                buttons.append(
                    {
                        "url": '/dashboard/cancel_order',
                        "label": 'Complete or cancel drive'
                    }
                )
                has_active_order = True
        elif is_driver:
            start_driving_url = '/dashboard/set_driver_available'
            start_driving_label = 'Start driving'
            buttons = [
                {'url': '/dashboard/history', 'label': 'See history'},
                {'url': '/dashboard/modify_user', 'label': 'Update information'},
            ]
            if request.user.driver.orders.filter(completed=False).exists():
                buttons.append(
                    {"url": '/dashboard/cancel_order',
                     "label": "Cancel current engagement"}
                )
            if request.user.driver.is_available:
                buttons.append(
                    {"url": '/dashboard/set_driver_unavailable',
                     "label": "Stop driving"}
                )
            else:
                buttons.extend(
                    [
                        {'url': start_driving_url, 'label': start_driving_label},
                    ]
                )
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
                                                   "is_available": is_available,
                                                   "orders": orders,
                                                   "features": features,
                                                   "cars": cars,
                                                   "now": datetime.now().strftime('%Y-%m-%dT%H:%M')
                                                   })

@login_required
@transaction.atomic
def call_driver(request):
    pickup_time_str = request.GET.get('time')
    departure = request.GET.get('departure')
    arrival = request.GET.get('arrival')
    car_id = request.GET.get('car')

    pickup_time = datetime.fromisoformat(pickup_time_str)
    # Get the car object based on the car id
    car_obj = get_object_or_404(Car, id=car_id)

    # Create a new order instance with the received data
    order = Order(customer=request.user.customer,
                  pickup_time=pickup_time,
                  pickup_latitude=departure.split(',')[0],
                  pickup_longitude=departure.split(',')[1],
                  dropoff_latitude=arrival.split(',')[0],
                  dropoff_longitude=arrival.split(',')[1],
                  car=car_obj)

    # Save the order instance to the database
    order.save()

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

@login_required
def set_driver_available(request):
    driver = request.user.driver
    driver.is_available = True
    driver.save()
    return redirect('index')

@login_required
def set_driver_unavailable(request):
    driver = request.user.driver
    driver.is_available = False
    driver.save()
    return redirect('index')

@login_required
@transaction.atomic
def confirm_order(request):
    order_id = request.GET['order_id']
    eta = request.GET['time_to_pickup']
    order = Order.objects.get(id=order_id)
    if hasattr(request.user, 'driver'):
        driver = request.user.driver
        order.assign_driver(driver)
        order.eta = eta
        order.save()
    return redirect('index')

@login_required
@transaction.atomic
def cancel_order(request):
    # get the current user
    user = request.user

    # check if the user is a driver or customer
    if hasattr(user, 'driver'):
        # if the user is a driver, unassign them from the order
        try:
            order = user.driver.orders.get(completed=False)
        except Order.DoesNotExist:
            # the driver doesn't have an active order
            return HttpResponseBadRequest('No active order found.')

        order.driver = None
        order.save()

        return redirect('index')

    elif hasattr(user, 'customer'):
        # if the user is a customer, mark the order as completed and unassign the driver
        try:
            order = user.customer.orders.get(completed=False)
        except Order.DoesNotExist:
            # the customer doesn't have an active order
            return HttpResponseBadRequest('No active order found.')

        order.completed = True
        order.driver = None
        order.save()

        return redirect('index')

    else:
        # the user is neither a driver nor a customer
        return HttpResponseBadRequest('User is not a driver or customer.')

@login_required
def add_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST)
        if form.is_valid():
            car = form.save(commit=False)
            car.customer = request.user.customer
            car.save()
            return redirect('index')
    else:
        form = CarForm()
    return render(request, 'add_car.html', {'form': form})

@login_required
def modify_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if car.customer.user == request.user:
        if request.method == 'POST':
            form = CarForm(request.POST, instance=car)
            if form.is_valid():
                form.save()
                return redirect('index')
        else:
            form = CarForm(instance=car)
        return render(request, 'modify_car.html', {'form': form})
    return JsonResponse({'success': False, 'message': 'You are not authorized to modify this car.'})

@login_required
def modify_user(request):
    user = request.user
    if request.method == 'POST':
        if hasattr(user, 'driver'):
            user_obj = user.driver
        elif hasattr(user, 'customer'):
            user_obj = user.customer
        else:
            return JsonResponse({'success': False, 'message': 'User is not a driver or customer.'})

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)

        if isinstance(user_obj, Driver):
            user_obj.latitude = request.POST.get('latitude', user_obj.latitude)
            user_obj.longitude = request.POST.get('longitude', user_obj.longitude)
            user_obj.license_number = request.POST.get('license_number', user_obj.license_number)
            user_obj.bank_account_info = request.POST.get('bank_account_info', user_obj.bank_account_info)
        elif isinstance(user_obj, Customer):
            user_obj.saved_payment_info = request.POST.get('saved_payment_info', user_obj.saved_payment_info)

        user.save()
        user_obj.save()
        return redirect('index')
    else:
        if hasattr(user, 'customer'):
            form = CustomerForm(instance=user.customer)
        elif hasattr(user, 'driver'):
            form = DriverForm(instance=user.driver)
        else:
            # If the user is not a Customer or a Driver, return an error message
            return render(request, 'error.html', {'error': 'You must be a Customer or a Driver'})
    return render(request, 'modify_user.html', {'form': form})
