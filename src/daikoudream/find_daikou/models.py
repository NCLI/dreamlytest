from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """ A custom user model to extend the default Django user model. """

    is_driver = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)

class Customer(models.Model):
    """ A model to represent a customer. """

    user = models.OneToOneField(
        'find_daikou.CustomUser',
        on_delete=models.CASCADE,
        related_name='customer'
    )
    saved_payment_info = models.CharField(max_length=4096)

class Car(models.Model):
    """ A model to represent a car. """

    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    customer = models.ForeignKey(
        'find_daikou.Customer',
        on_delete=models.CASCADE,
        related_name='cars'
    )

class Driver(models.Model):
    """ A model to represent a driver. """

    user = models.OneToOneField(
        'find_daikou.CustomUser',
        on_delete=models.CASCADE,
        related_name='driver'
    )
    is_active = models.BooleanField(default=False)
    latitude = models.FloatField()
    longitude = models.FloatField()
    license_number = models.CharField(max_length=50)
    bank_account_info = models.CharField(max_length=4096)

class Order(models.Model):
    """ A model to represent an order. """

    customer = models.ForeignKey(
        'find_daikou.Customer',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    driver = models.ForeignKey(
        'find_daikou.Driver',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    car = models.ForeignKey(
        'find_daikou.Car',
        on_delete=models.CASCADE
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()
    completed = models.BooleanField(default=False)
