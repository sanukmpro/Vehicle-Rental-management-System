from django.db import models

# Create your models here.
class Users(models.Model):
    id = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=200)
    privilage = models.CharField(null=True,max_length=50)

   
class Driver(models.Model):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    status = models.CharField(max_length=20)
    photo = models.ImageField(upload_to="media/drivers/")
    vehicle_types = models.TextField(null=True)

class Vehicle(models.Model):

    vehicle_name = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=50)
    brand = models.CharField(max_length=100)
    rent_price = models.IntegerField()
    fuel_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    vehicle_image = models.ImageField(upload_to="vehicles/")
    VEHICLE_TYPES = [
        ("2W", "Two Wheeler"),
        ("3W", "Three Wheeler"),
        ("4W", "Four Wheeler"),
        ("HV", "Heavy Vehicle"),
    ]
    vehicle_type = models.CharField(null=True, max_length=10, choices=VEHICLE_TYPES)

class VehicleBooking(models.Model):
    # Left-side info
    WHEEL_CHOICES = [
        ('2W', 'Two Wheeler'),
        ('3W', 'Three Wheeler'),
        ('4W', 'Four Wheeler'),
        ('HV', 'Heavy Vehicle'),
    ]
    brand = models.CharField(max_length=50)
    vehicle_name = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=2, choices=WHEEL_CHOICES)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)
    vehicle_number = models.CharField(max_length=20)
    
    # Right-side booking info
    booking_date = models.DateField()
    booking_time = models.TimeField()
    num_days = models.PositiveIntegerField(default=1)
    DRIVER_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    driver_needed = models.CharField(max_length=3, choices=DRIVER_CHOICES)
    
    # Store user's email from session
    email = models.EmailField()
    driver_accepted=models.BooleanField(default=False)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    def __str__(self):
        return f"{self.email} booked {self.brand} {self.vehicle_name} on {self.booking_date}"
    
    @property
    def total_rent(self):
        return self.num_days * self.rent_price

class DriverRequests(models.Model):
    requester_email = models.EmailField()
    vehicle_name = models.CharField(max_length=50,null=True)
    WHEEL_CHOICES = [
        ('2W', 'Two Wheeler'),
        ('3W', 'Three Wheeler'),
        ('4W', 'Four Wheeler'),
        ('HV', 'Heavy Vehicle'),
    ]
    vehicle_type = models.CharField(max_length=2, choices=WHEEL_CHOICES)
    lowest_bid = models.IntegerField(default=0,null=True)
    lowest_bidder_email= models.EmailField(null=True)
    user_accepted = models.BooleanField(null=True,default=False)

class Bids(models.Model):
    vehicle_name = models.CharField(max_length=50)
    requester_email = models.EmailField()
    bidder = models.EmailField()
    bid_amount = models.IntegerField()

    
class Notification(models.Model):
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.message[:30]}"