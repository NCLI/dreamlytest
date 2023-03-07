"""daikoudream URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.contrib.auth.views import LoginView, LogoutView

import find_daikou.views as views

urlpatterns = [
    path('', views.index, name='index'),
    path('test/', views.available_drivers, name='driverlist'),
    path('confirm_order', views.confirm_order, name='confirm_order'),
    path('call_driver/', views.call_driver, name='call_driver'),
    # path('modify_driver/', views.modify_driver, name='modify_driver'),
    path('modify_car/', views.modify_car, name='modify_car'),
    path('add_car/', views.add_car, name='add_car'),
    path('modify_user/', views.modify_user, name='modify_user'),
    path('history/', views.history, name='history'),
    # path('open_orders', views.open_orders, name='open_orders'),
    path('set_driver_available/', views.set_driver_available, name='set_driver_available'),
    path('set_driver_unavailable/', views.set_driver_unavailable, name='set_driver_unavailable'),
    path('cancel_order/', views.cancel_order, name='cancel_order'),
    path('update_eta/', views.update_eta, name='update_eta'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
]
