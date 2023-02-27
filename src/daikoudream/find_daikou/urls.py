from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('test/', views.available_drivers, name='driverlist'),
    path('call_driver/', views.call_driver, name='call_driver'),
]
