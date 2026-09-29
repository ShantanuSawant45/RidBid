
from django.contrib.auth.models import AbstractUser
from django.db import models

class Role(models.TextChoices):
    RIDER = 'rider', 'Rider'
    DRIVER = 'driver', 'Driver'
    RIDER_DRIVER= "rider_driver", 'Rider and Driver'

class VehicleType(models.TextChoices):
    car="car",'Car'
    bike="bike",'Bike'
    suv="suv",'SUV'
    van="van",'Van'
    truck="truck",'Truck'

class User(AbstractUser):
    role = models.CharField(max_length=30,choices=Role.choices, default=Role.RIDER)
    phone=models.CharField(max_length=30,null=True,blank=True, unique=True)
    profile_picture_url=models.URLField(blank=True, null=True)
    is_verified=models.BooleanField(default=False)
    last_login_at= models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.email} ({self.role})"



class DriverDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_detail")
    license_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    vehicle_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    vehicle_type = models.CharField(max_length=10, choices=VehicleType.choices, null=True, blank=True)
    vehicle_model = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Driver: {self.user.email}"


class RiderDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="rider_detail")
    rating = models.FloatField(default=0.0)
    default_payment_method_id = models.CharField(max_length=50, blank=True, null=True)
    home_address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Rider: {self.user.email}"    