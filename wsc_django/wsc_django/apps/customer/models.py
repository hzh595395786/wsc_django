from django.db import models

# Create your models here.

from shop.models import Shop
from user.models import User
from wsc_django.utils.models import TimeBaseModel


class Customer(TimeBaseModel):
    """客户模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="客户对应的店铺对象")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="客户对应的用户对象")
    create_date = models.DateField(null=False, auto_now_add=True, verbose_name="客户新增日期")
    consume_amount = models.DecimalField(max_digits=13, decimal_places=4, default=0, verbose_name="消费金额")
    consume_count = models.IntegerField(default=0, verbose_name="消费次数")
    point = models.DecimalField(max_digits=13, decimal_places=4, default=0, verbose_name="积分")
    remark = models.CharField(max_length=64, default="", verbose_name="备注")

    class Meta:
        db_table = "customer"
        verbose_name = "客户"
        verbose_name_plural = verbose_name

    def is_new_customer(self):
        return not bool(self.consume_count)


class CustomerPoint(TimeBaseModel):
    """客户历史积分模型类"""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False, verbose_name="对应客户对象")
    point_change = models.DecimalField(max_digits=13, decimal_places=4, verbose_name="积分变更量")
    create_time = models.DateTimeField(auto_now_add=True, null=False, verbose_name="创建时间")
    current_point = models.DecimalField(max_digits=13, decimal_places=4, verbose_name="历史时刻当前积分")
    type = models.SmallIntegerField(null=False, default=0, verbose_name="变更类型(预留)")

    class Meta:
        db_table = "customer_point"
        verbose_name = "客户历史积分"
        verbose_name_plural = verbose_name
