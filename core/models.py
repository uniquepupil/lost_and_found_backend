from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone    
import random
from django.conf import settings



class CustomUserManager(BaseUserManager):
    """
    Custom manager for User model with no username field, only email.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.
    """
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15, unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'mobile_number']

    def __str__(self):
        return self.email

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp_code = str(random.randint(100000, 999999))
        self.save()

class LostItem(models.Model):
    name = models.CharField(max_length=255)  # To store the name fetched from localStorage
    mobile_number = models.CharField(max_length=15)  # To store the mobile number fetched from localStorage
    location = models.CharField(max_length=255)  # Location where the item was lost
    lost_item_name = models.CharField(max_length=255)  # Name of the lost item
    description = models.TextField()  # Description of the lost item
    date_lost = models.DateField()  # Date when the item was lost (dd/mm/yyyy format)
    image = models.ImageField(upload_to='lost_items/', null=True, blank=True)  # Image of the lost item
    
    def __str__(self):
        return f"Lost Item: {self.lost_item_name} by {self.name}"

    class Meta:
        verbose_name = 'Lost Item'
        verbose_name_plural = 'Lost Items'

class FoundItem(models.Model):
    name = models.CharField(max_length=255)  # Name of the person who found the item
    mobile_number = models.CharField(max_length=15)  # Mobile number of the person who found the item
    location = models.CharField(max_length=255)  # Location where the item was found
    found_item_name = models.CharField(max_length=255)  # Name of the found item
    description = models.TextField()  # Description of the found item
    date_found = models.DateField()  # Date when the item was found (dd/mm/yyyy format)
    image = models.ImageField(upload_to='found_items/', null=True, blank=True)  # Image of the found item
    
    def __str__(self):
        return f"Found Item: {self.found_item_name} by {self.name}"

    class Meta:
        verbose_name = 'Found Item'
        verbose_name_plural = 'Found Items'
