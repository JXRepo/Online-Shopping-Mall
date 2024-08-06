from django.db import models

# Create your models here.
from django.db import models
from apps.orders.models import OrderInfo
from utils.models import BaseModel

class Payment(BaseModel):
    """Payment Information"""
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, verbose_name='Order')
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name="Payment Number")

    class Meta:
        db_table = 'tb_payment'
        verbose_name = 'Payment Information'
        verbose_name_plural = verbose_name