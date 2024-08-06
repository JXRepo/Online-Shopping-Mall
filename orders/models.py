from django.db import models

# Create your models here.
from django.db import models
from apps.goods.models import SKU
from apps.users.models import User, Address
from utils.models import BaseModel


class OrderInfo(BaseModel):
    """order information"""
    PAY_METHODS_ENUM = {
        "CASH": 1,
        "ALIPAY": 2
    }
    PAY_METHOD_CHOICES = (
        (1, "Cash on delivery"),
        (2, "Alipay"),
    )
    ORDER_STATUS_ENUM = {
        "UNPAID": 1,
        "UNSEND": 2,
        "UNRECEIVED": 3,
        "UNCOMMENT": 4,
        "FINISHED": 5
    }
    ORDER_STATUS_CHOICES = (
        (1, "To be paid"),
        (2, "to be delivered"),
        (3, "Waiting for receipt"),
        (4, "Be evaluated"),
        (5, "completed"),
        (6, "Cancelled"),
    )
    order_id = models.CharField(max_length=64, primary_key=True, verbose_name="order number")
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Ordering user")
    address = models.ForeignKey(Address, on_delete=models.PROTECT, verbose_name="Shipping address")
    total_count = models.IntegerField(default=1, verbose_name="Total number of products")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total amount of goods")
    freight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="freight")
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name="payment method")
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name="Order Status")

    class Meta:
        db_table = "tb_order_info"
        verbose_name = 'Basic order information'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.order_id


class OrderGoods(BaseModel):
    """Order Items"""
    SCORE_CHOICES = (
        (0, '0 points'),
        (1, '20 points'),
        (2, '40 points'),
        (3, '60 points'),
        (4, '80 points'),
        (5, '100 points'),
    )
    order = models.ForeignKey(OrderInfo, related_name='skus', on_delete=models.CASCADE, verbose_name="Order")
    sku = models.ForeignKey(SKU, on_delete=models.PROTECT, verbose_name="Order Items")
    count = models.IntegerField(default=1, verbose_name="quantity")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="unit price")
    comment = models.TextField(default="", verbose_name="Evaluation information")
    score = models.SmallIntegerField(choices=SCORE_CHOICES, default=5, verbose_name='Satisfaction Rating')
    is_anonymous = models.BooleanField(default=False, verbose_name='Anonymous evaluation')
    is_commented = models.BooleanField(default=False, verbose_name='Have you evaluated')

    class Meta:
        db_table = "tb_order_goods"
        verbose_name = 'Order Items'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku.name