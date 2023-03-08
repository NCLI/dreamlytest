from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    """ A custom user model to extend the default Django user model. """

class Customer(models.Model):
    """ A model to represent a customer. """

    address = models.CharField(max_length=1024)
    phone = models.CharField(max_length=32)

    user = models.OneToOneField(
        'find_daikou.CustomUser',
        on_delete=models.CASCADE,
        related_name='customer'
    )
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

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
    def __str__(self):
        return f"{self.make} {self.model} {self.year}"

class Driver(models.Model):
    """ A model to represent a driver. """

    user = models.OneToOneField(
        'find_daikou.CustomUser',
        on_delete=models.CASCADE,
        related_name='driver'
    )
    is_available = models.BooleanField(default=False)
    latitude = models.FloatField(
        default = 0.0
    )
    longitude = models.FloatField(
        default = 0.0
    )
    def __str__(self):
        return self.user.username

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
        related_name='orders',
        null=True,
        blank=True
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
    eta = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.completed:
            # check if there are any existing incomplete orders associated with the customer
            existing_orders = Order.objects.filter(customer=self.customer, completed=False).exclude(id=self.id)
            if self.driver != None:
               existing_orders_driver = Order.objects.filter(driver=self.driver, completed=False).exclude(id=self.id)
               if existing_orders_driver.exists():
                   raise ValidationError('A driver can only have one incomplete order at a time.')
            existing_orders_user = Order.objects.filter(customer=self.customer, completed=False).exclude(id=self.id)
            # check if the car belongs to the user associated with the order
            if self.car not in self.customer.cars.all():
                raise ValidationError('The selected car does not belong to the customer.')
            if existing_orders_user.exists():
                raise ValidationError('A customer can only have one incomplete order at a time.')
        super().save(*args, **kwargs)

    def complete_order(self):
        self.completed = True
        self.save()
        return True

    def assign_driver(self, driver):
        self.driver = driver
        self.save()

    def unassign_driver(self):
        self.driver = None
        self.eta = None
        self.save()
