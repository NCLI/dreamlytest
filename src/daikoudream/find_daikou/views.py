from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point

from find_daikou.models import Driver
from .forms import DriverForm


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

def index(request):
    """ A view to display all active drivers on a map. """
    context = {}

    return render(request, 'active_drivers.html', context)

@login_required
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save(commit=False)
            driver.user = request.user
            driver.save()
            messages.success(request, 'Driver added successfully!')
            return redirect('driver_detail', pk=driver.pk)
    else:
        form = DriverForm()
    return render(request, 'add_driver.html', {'form': form})
