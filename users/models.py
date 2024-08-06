from django.db import models

# Create your models here.

# 1. Define your own model
# We need to encrypt the password and verify the password when logging in.
# class User(models.Model):
#     username=models.CharField(max_length=20,unique=True)
#     password=models.CharField(max_length=20)
#     mobile=models.CharField(max_length=11,unique=True)

# 2. django Comes with a user model
# This user model has password encryption and password verification
# from django.contrib.auth.models import User

from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    mobile=models.CharField(max_length=11,unique=True)
    email_active = models.BooleanField(default=False, verbose_name='Email Verification Status')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='default address')

    # addresses
    class Meta:
        db_table='tb_users'
        verbose_name='User Management'
        verbose_name_plural=verbose_name


from utils.models import BaseModel

class Address(BaseModel):
    """User Address"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='user')
    title = models.CharField(max_length=20, verbose_name='Address Name')
    receiver = models.CharField(max_length=20, verbose_name='Receiver')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='Province')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='city')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='district')
    place = models.CharField(max_length=50, verbose_name='address')
    mobile = models.CharField(max_length=11, verbose_name='cell phone')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='Fixed telephone')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='E-mail')
    is_deleted = models.BooleanField(default=False, verbose_name='Tombstone')

    class Meta:
        db_table = 'tb_address'
        verbose_name = 'User Address'
        verbose_name_plural = verbose_name
        ordering = ['-update_time']