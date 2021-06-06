from django.db import models

# Create your models here.
from customer.constant import MineAddressDefault, MineAddressStatus
from shop.models import Shop
from user.constant import Sex
from user.models import User
from wsc_django.utils.core import FormatAddress
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


class MineAddress(TimeBaseModel):
    """我的地址模型类"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="address", null=False, verbose_name="顾客ID")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="address", null=False, verbose_name="顾客ID")
    province = models.IntegerField(verbose_name="省份编号")
    city = models.IntegerField(verbose_name="城市编号")
    county = models.IntegerField(verbose_name="区编号")
    address = models.CharField(max_length=64, null=False, verbose_name="详细地址")
    longitude = models.DecimalField(null=True, max_digits=10, decimal_places=4, verbose_name="经度")
    latitude = models.DecimalField(null=True, max_digits=10, decimal_places=4, verbose_name="纬度")
    name = models.CharField(max_length=32, null=False, verbose_name="顾客姓名")
    sex = models.SmallIntegerField(null=False, default=Sex.UNKNOWN, verbose_name="顾客性别,0:未知1:男2:女")
    phone = models.CharField(max_length=32, default="", verbose_name="顾客手机号")
    default = models.SmallIntegerField(default=MineAddressDefault.NO, verbose_name="是否为默认地址")
    status = models.SmallIntegerField(default=MineAddressStatus.NORMAL, verbose_name="状态,0:删除1:正常")

    class Meta:
        db_table = "mine_address"
        verbose_name = "我的地址"
        verbose_name_plural = verbose_name

    @property
    def full_address(self):
        return FormatAddress.get_format_address(
            self.province, self.city, self.county, self.address
        )
