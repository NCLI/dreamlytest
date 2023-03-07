from django.urls import path

from . import views

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
]
