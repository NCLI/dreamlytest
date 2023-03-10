from typing import List, Dict, Any, Union, Optional

from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponseBadRequest, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.db import transaction
from django.urls import reverse
from django.db.models.query import QuerySet

from find_daikou.models import Driver, Order, Car
from .forms import DriverForm, RegistrationForm, CarForm, CustomerForm
from .models import Driver, Customer

def available_drivers(request) -> JsonResponse:
    """
    Returns a JSON response containing a list of available drivers as GeoJSON points.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response containing a list of available drivers as GeoJSON points.
    """

    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Attempt to retrieve the current order and assigned driver, if any
        try:
            order = Order.objects.get(customer=request.user.customer, completed=False)
            assigned_driver = order.driver
        except Order.DoesNotExist:
            assigned_driver = None
    else:
        assigned_driver = None

    # Retrieve all drivers that are currently available
    drivers = Driver.objects.filter(is_available=True)

    # Create a GeoJSON FeatureCollection of driver points
    driver_points = [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [d.latitude, d.longitude]},
            'properties': {'name': d.user.username, 'is_assigned': d == assigned_driver }
        } for d in drivers
    ]

    # Create a dictionary containing the GeoJSON FeatureCollection
    data = {
        'type': 'FeatureCollection',
        'features': driver_points
    }

    # Return the response as a JSON object
    return JsonResponse(data)

def register(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """
    A view responsible for user registration.

    Args:
        request (HttpRequest): An HTTP request object representing the incoming request.

    Returns:
        Union[HttpResponse, HttpResponseRedirect]: An HTTP response object representing the outgoing response.
    """
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

def index(request: HttpRequest) -> HttpResponse:
    """
    The center of the Find Daikou experiential extravaganza.

    Args:
        request (HttpRequest): An HTTP request object representing the incoming request.

    Returns:
        HttpResponse: An HTTP response object representing the outgoing response.
    """
    is_customer = False
    is_driver = False
    has_active_order = False
    is_available = False
    orders = []
    features = []
    cars =[]
    eta = None

    if request.user.is_authenticated:
        user_type = get_user_type(request.user)
        if user_type == 'customer':
            is_customer = True
            cars = Car.objects.filter(customer=request.user.customer)
        elif user_type == 'driver':
            is_driver = True
            if request.user.driver.is_available:
                is_available = True

            orders = Order.objects.filter(driver=None, completed=False)
            features = create_order_features(orders)

        # Set button labels and URLs

        # Set active order details
        if is_customer:
            active_order = get_active_order(request.user.customer.orders)
            if active_order:
                has_active_order = True
                eta = active_order.eta
        elif is_driver:
            active_order = get_active_order(request.user.driver.orders)
        buttons = create_buttons(user_type, request.user, has_active_order)

    else:
        buttons = create_buttons('anonymous', None, False)

    return render(request, 'active_drivers.html', {
        "buttons": buttons,
        "is_customer": is_customer,
        "has_active_order": has_active_order,
        "is_driver": is_driver,
        "is_available": is_available,
        "orders": orders,
        "features": features,
        "cars": cars,
        "now": datetime.now().strftime('%Y-%m-%dT%H:%M'),
        "eta": eta,
    })

def get_user_type(user: Any) -> str:
    """
    Determine the user type based on the user object.

    Args:
    - user: A user object.

    Returns:
    - A string indicating the user type.
    """
    if hasattr(user, 'customer'):
        return 'customer'
    elif hasattr(user, 'driver'):
        return 'driver'
    else:
        return 'anonymous'

def get_active_order(orders: QuerySet) -> Optional[Order]:
    """
    Return the first active order in the given query set of orders.
    Safeguard, just in case a user magically manages to have two active orders.

    Args:
    - orders: A query set of orders.

    Returns:
    - The first active order in the query set, or None if there are no active orders.
    """
    active_orders = orders.filter(completed=False)
    if active_orders.exists():
        return active_orders.first()
    return None

def create_order_features(orders: QuerySet) -> List[Dict[str, Union[str, Dict[str, Union[str, List[float]]]]]]:
    """
    Create a list of features for all orders in the given query set.

    Args:
    - orders: A query set of orders.

    Returns:
    - A list of features, where each feature is a dictionary with the following keys:
      - 'type': A string indicating the type of the feature, which is 'Feature' in this case.
      - 'geometry': A dictionary representing the geometry of the feature, which has the following keys:
        - 'type': A string indicating the type of the geometry, which is 'Point' in this case.
        - 'coordinates': A list of two floating point numbers representing the coordinates of the feature.
      - 'properties': A dictionary containing additional properties of the feature, which has the following keys:
        - 'id': An integer indicating the ID of the order.
        - 'type': A string indicating the type of the order, which is either 'pickup' or 'dropoff'.
        - 'description': A string describing the feature.
    """
    features = []
    for order in orders:
        pickup_location = Point(order.pickup_latitude, order.pickup_longitude)
        pickup_feature = create_point_feature(pickup_location, order.id, 'pickup')
        features.append(pickup_feature)

        dropoff_location = Point(order.dropoff_latitude, order.dropoff_longitude)
        dropoff_feature = create_point_feature(dropoff_location, order.id, 'dropoff')
        features.append(dropoff_feature)
    return features


def create_point_feature(location: Union[object, Dict[str, float]], order_id: str, order_type: str) -> Dict[str, Union[str, Dict[str, Union[str, List[float]]], Dict[str, str]]]:
    """
    Create a GeoJSON feature object representing a point.

    Args:
        location (object or dict): A location object with `x` and `y` coordinates or a dictionary with keys `x` and `y`
            containing the coordinates.
        order_id (str): The ID of the order.
        order_type (str): The type of the order.

    Returns:
        A dictionary representing the GeoJSON feature object.

    """
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [location.x, location.y]
        },
        'properties': {
            'id': order_id,
            'type': order_type,
            'description': "Pointy"
        }
    }

def create_buttons(user_type: str, user: object, has_active_order: bool) -> List[Dict[str, str]]:
    """
    Create a list of buttons for the user interface.

    Args:
        user_type (str): The type of user. One of "customer", "driver", "anonymous", or "other".
        user (object): The user object.
        has_active_order (bool): A flag indicating whether the user has an active order.

    Returns:
        A list of dictionaries representing the buttons.

    """
    buttons = []
    if user_type == "customer":
        buttons = [
            {'url': reverse('history'), 'label': 'See history'},
            {'url': reverse('add_car'), 'label': 'Add car'},
            {'url': reverse('modify_user'), 'label': 'Update information'},
        ]
        if has_active_order:
            buttons.append(
                {
                    "url": reverse('cancel_order'),
                    "label": 'Complete or cancel drive'
                }
            )
    elif user_type == "driver":
        is_available = user.driver.is_available if hasattr(user, "driver") else False
        buttons = [
            {'url': reverse('history'), 'label': 'See history'},
            {'url': reverse('modify_user'), 'label': 'Update information'},
        ]
        if user.driver.orders.filter(completed=False).exists():
            buttons.extend([
                {"url": reverse('cancel_order'),
                 "label": "Cancel current engagement"},
                {"url": reverse('update_eta'),
                 "label": "Update ETA"},
                ]
            )
        if is_available:
            buttons.append(
                {"url": reverse('set_driver_unavailable'),
                 "label": "Stop driving"}
            )
        else:
            buttons.extend(
                [
                    {"url": reverse('set_driver_available'),
                    "label": "Start driving"}
                ]
            )
    if user_type == "anonymous":
        buttons = [
            {'url': reverse('login'), 'label': 'Log in'},
            {'url': reverse('register'), 'label': 'Register'},
        ]


    else:
        buttons.append(
            {'url': reverse('logout'), 'label': 'Logout'},
        )
    return buttons

@login_required
@transaction.atomic
def call_driver(request: HttpRequest) -> HttpResponse:
    """
    View function that handles a customer's request to book a ride with a driver.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that redirects the user to the homepage upon successful booking of a ride.
    """
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
def history(request: HttpRequest) -> HttpResponse:
    """
    View function that displays a user's order history.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that renders a template showing the user's order history.
    """
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
def set_driver_available(request: HttpRequest) -> HttpResponse:
    """
    View function that sets a driver's availability status to True.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that redirects the user to the homepage.
    """
    driver = request.user.driver
    driver.is_available = True
    driver.save()
    return redirect('index')

@login_required
def set_driver_unavailable(request: HttpRequest) -> HttpResponse:
    """
    View function that sets a driver's availability status to False.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that redirects the user to the homepage.
    """
    driver = request.user.driver
    driver.is_available = False
    driver.save()
    return redirect('index')

@login_required
@transaction.atomic
def confirm_order(request: HttpRequest) -> HttpResponse:
    """
    View function that confirms a driver's acceptance of an order and assigns the driver to the order.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that redirects the user to the homepage upon successful confirmation of an order.
    """
    order_id = request.GET['order_id']
    time_to_pickup = int(request.GET['time_to_pickup'])
    order = Order.objects.get(id=order_id)
    if hasattr(request.user, 'driver'):
        driver = request.user.driver
        order.assign_driver(driver)
        order.eta = datetime.now() + timedelta(minutes=time_to_pickup)
        order.save()
    return redirect('index')

@login_required
@transaction.atomic
def cancel_order(request: HttpRequest) -> HttpResponse:
    """
    View function that cancels an order and unassigns the driver from the order.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that redirects the user to the homepage upon successful cancellation of an order.
    """
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

        order.unassign_driver()

        return redirect('index')

    elif hasattr(user, 'customer'):
        # if the user is a customer, mark the order as completed and unassign the driver
        try:
            order = user.customer.orders.get(completed=False)
        except Order.DoesNotExist:
            # the customer doesn't have an active order
            return HttpResponseBadRequest('No active order found.')

        order.complete_order()

        return redirect('index')

    else:
        # the user is neither a driver nor a customer
        return HttpResponseBadRequest('User is not a driver or customer.')

@login_required
def add_car(request: HttpRequest) -> HttpResponse:
    """
    View function that allows a user to add a car to their profile.

    Args:
    - request: The HTTP request object.

    Returns:
    - An HTTP response object that renders a template showing a form to add a car.
    """
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
def modify_user(request: HttpRequest) -> Union[HttpResponse, JsonResponse]:
    """
    Allows a logged-in user to modify their account information.
    """
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
        user.password = user.password
        user.username = user.username

        if isinstance(user_obj, Driver):
            user_obj.latitude = request.POST.get('latitude', user_obj.latitude)
            user_obj.longitude = request.POST.get('longitude', user_obj.longitude)
        else:
            user_obj.address = request.POST.get('address', user_obj.address)
            user_obj.phone = request.POST.get('phone', user_obj.phone)

        user_obj.save()
        user.save()
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

@login_required
@transaction.atomic
def update_eta(request: HttpRequest) -> Union[HttpResponse, HttpResponseRedirect]:
    """
    Allows a logged-in driver to update the estimated time of arrival (ETA) for the order they are currently delivering.
    """
    user = request.user
    order = get_object_or_404(Order, driver=user.driver, completed=False)

    if request.method == 'POST':
        # Get the minutes input from the form
        minutes = int(request.POST.get('minutes'))

        # Calculate the new ETA
        eta = datetime.now() + timedelta(minutes=minutes)

        # Update the Order object with the new ETA
        order.eta = eta
        order.save()

        # Redirect to the order detail page
        return redirect('index')

    return render(request, 'update_eta.html', {'order': order})
