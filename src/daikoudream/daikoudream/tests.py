from django.core.exceptions import ValidationError
from django.test import TestCase
from datetime import datetime, timedelta, timezone
from django.utils import timezone
from find_daikou.models import CustomUser, Customer, Car, Driver, Order


class CustomUserModelTest(TestCase):
    def test_create_user(self):
        user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password",
        )
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "testuser@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        superuser = CustomUser.objects.create_superuser(
            username="superuser",
            email="superuser@example.com",
            password="password",
        )
        self.assertIsInstance(superuser, CustomUser)
        self.assertEqual(superuser.username, "superuser")
        self.assertEqual(superuser.email, "superuser@example.com")
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class CustomerModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password",
        )
        self.customer = Customer.objects.create(
            user=self.user,
            saved_payment_info="test payment info",
        )

    def test_create_customer(self):
        self.assertIsInstance(self.customer, Customer)
        self.assertEqual(self.customer.user, self.user)
        self.assertEqual(self.customer.saved_payment_info, "test payment info")


class CarModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="password",
        )
        self.customer = Customer.objects.create(
            user=self.user,
            saved_payment_info="test payment info",
        )
        self.car = Car.objects.create(
            make="Toyota",
            model="Corolla",
            year=2021,
            customer=self.customer,
        )

    def test_create_car(self):
        self.assertIsInstance(self.car, Car)
        self.assertEqual(self.car.make, "Toyota")
        self.assertEqual(self.car.model, "Corolla")
        self.assertEqual(self.car.year, 2021)
        self.assertEqual(self.car.customer, self.customer)

class DriverTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(username='testdriver')
        self.driver = Driver.objects.create(user=self.user, is_available=True, latitude=0.0, longitude=0.0,
                                             license_number='ABC123', bank_account_info='test bank info')

    def test_str(self):
        self.assertEqual(str(self.driver), 'testdriver')

    def test_assign_order(self):
        user = CustomUser.objects.create(username='testcustomer')
        customer = Customer.objects.create(user=user, saved_payment_info='test payment info')
        car = Car.objects.create(make='Test', model='Car', year=2022, customer=customer)
        order = Order.objects.create(customer=customer, car=car, pickup_latitude=0.0, pickup_longitude=0.0,
                                     dropoff_latitude=1.0, dropoff_longitude=1.0, pickup_time=timezone.now(),
                                     completed=False)
        self.driver.orders.add(order)
        self.assertEqual(self.driver.orders.count(), 1)

class OrderModelTestCase(TestCase):

    def setUp(self):
        # Create a user for the customer and assign it to a customer instance
        self.user0 = CustomUser.objects.create_user(username="testuser0", password="testpass0")
        self.user1 = CustomUser.objects.create_user(username="testuser1", password="testpass1")
        self.customer0 = Customer.objects.create(user=self.user0, saved_payment_info="1234 5678 9101 1121")
        self.customer1 = Customer.objects.create(user=self.user1, saved_payment_info="1234 5678 9101 1121")
        
        # Create a user for the driver and assign it to a driver instance
        self.user2 = CustomUser.objects.create_user(username="testuser2", password="testpass2")
        self.driver0 = Driver.objects.create(user=self.user2, is_available=True, latitude=35.12345, 
                                              longitude=139.12345, license_number="123456", 
                                              bank_account_info="1234 5678 9101 1121")
        self.user3 = CustomUser.objects.create_user(username="testuser3", password="testpass3")
        self.driver1 = Driver.objects.create(user=self.user3, is_available=True, latitude=35.12345, 
                                              longitude=139.12345, license_number="123456", 
                                              bank_account_info="1234 5678 9101 1121")
        
        # Create a car for the customer
        self.car0 = Car.objects.create(make="Toyota", model="Camry", year=2021, customer=self.customer0)
        self.car1 = Car.objects.create(make="Toyota", model="Camry", year=2021, customer=self.customer1)
        
        # Create an order associated with the customer and car
        self.order0 = Order.objects.create(customer=self.customer0, car=self.car0, 
                                            pickup_latitude=35.12345, pickup_longitude=139.12345,
                                            dropoff_latitude=35.67890, dropoff_longitude=139.67890,
                                            pickup_time=timezone.now(), completed=False)
        self.order1 = Order.objects.create(customer=self.customer1, car=self.car1, 
                                            pickup_latitude=35.12345, pickup_longitude=139.12345,
                                            dropoff_latitude=35.67890, dropoff_longitude=139.67890,
                                            pickup_time=timezone.now(), completed=False)

    def test_order_creation(self):
        # Test that the orders were created successfully
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(self.order0.customer, self.customer0)
        self.assertEqual(self.order0.car, self.car0)
        self.assertEqual(self.order0.completed, False)

    def test_driver_assignment(self):
        # Test that a driver can be assigned to an order successfully
        self.order0.assign_driver(self.driver0)
        self.assertEqual(self.order0.driver, self.driver0)

    def test_driver_assignment_failure(self):
        # Test that a driver can only be assigned to one order at a time
        self.order0.assign_driver(self.driver0)
        with self.assertRaises(ValidationError):
            self.order1.assign_driver(self.driver0)

    def test_car_belongs_to_customer(self):
        # Test that an order can only be associated with a car belonging to the customer
        self.user4 = CustomUser.objects.create_user(username="testuser4", password="testpass1")
        self.customer2 = Customer.objects.create(user=self.user4, saved_payment_info="1234 5678 9101 1121")
        self.car2 = Car.objects.create(make="Nissan", model="Altima", year=2022, customer=self.customer2)
        self.order2 = Order.objects.create(customer=self.customer2, car=self.car2, 
                                            pickup_latitude=35.12345, pickup_longitude=139.12345,
                                            dropoff_latitude=35.67890, dropoff_longitude=139.67890,
                                            pickup_time=timezone.now(), completed=False)
        self.order2.car = self.car2
        self.order2.save()
        self.assertEqual(self.order2.car, self.car2)
        self.order2.complete_order()

    def test_driver_unassignment(self):
        # Test that a driver can be unassigned from an order successfully
        self.order0.assign_driver(self.driver0)
        self.assertEqual(self.order0.driver, self.driver0)
        self.order0.unassign_driver()
        self.assertEqual(self.order0.driver, None)

    def test_order_completion(self):
        # Test that an order can be marked as completed successfully
        self.order0.assign_driver(self.driver0)
        self.order0.complete_order()
        self.assertEqual(self.order0.completed, True)
