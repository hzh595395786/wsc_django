import decimal

from django.db import models

# Create your models here.
from shop.models import Shop
from wsc_django.utils.models import TimeBaseMixin
from wsc_django.apps.order.constant import OrderDeliveryMethod
from .constant import (
    DeliveryType,
)


class Delivery(models.Model, TimeBaseMixin):
    """配送记录模型类"""

    delivery_type = models.SmallIntegerField(
        null=False,
        default=DeliveryType.ExpressDelivery,
        verbose_name="配送方式",
    )
    company = models.CharField(max_length=32, verbose_name="快递公司,仅在配送方式为快递时才有")
    express_num = models.CharField(max_length=32, verbose_name="快递单号,仅在配送方式为快递时才有")

    class Meta:
        db_table = "delivery"
        verbose_name = "配送记录"
        verbose_name_plural = verbose_name


class DeliveryConfig(models.Model, TimeBaseMixin):
    """订单配送配置模型类"""

    id = models.ForeignKey(
        Shop,
        primary_key=True,
        null=False,
        on_delete=models.CASCADE,
        verbose_name="店铺id"
    )
    # 配送模式
    home_on = models.BooleanField(null=False, default=True, verbose_name="配送模式是否开启")
    home_minimum_order_amount = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        default=0,
        verbose_name="配送模式起送金额",
    )
    home_delivery_amount = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        default=0,
        verbose_name="配送模式配送费",
    )
    home_minimum_free_amount = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        default=0,
        verbose_name="配送模式免配送费最小金额",
    )
    # 自提模式
    pick_on = models.BooleanField(null=False, default=True, verbose_name="自提模式是否开启")
    pick_service_amount = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        default=0,
        verbose_name="自提模式服务费",
    )
    pick_minimum_free_amount = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        default=0,
        verbose_name="自提模式免服务费最小金额",
    )
    pick_today_on = models.BooleanField(null=False, default=True, verbose_name="今天自提是否开启")
    pick_tomorrow_on = models.BooleanField(null=False, default=True, verbose_name="明天自提是否开启")

    class Meta:
        db_table = "delivery_config"
        verbose_name = "配送配置"
        verbose_name_plural = verbose_name

    def limit(self, delivery_method, order_amount):
        """
        订单配送限制

        :param delivery_method: 配送方式
        :param order_amount: 订单总价
        :return:
        """
        if (
            delivery_method == OrderDeliveryMethod.HOME_DELIVERY
            and self.home_minimum_order_amount > order_amount
        ):
            return False
        return True

    def calculate(self, delivery_method, order_amount):
        """
        订单优惠计算，返回运费可以优惠的金额

        :param delivery_method: 配送方式
        :param order_amount: 订单总价
        :return:
        """
        if delivery_method == OrderDeliveryMethod.HOME_DELIVERY:
            if order_amount < self.home_minimum_free_amount:
                result = decimal.Decimal(0)
            else:
                result = self.home_delivery_amount
        else:
            if order_amount < self.pick_minimum_free_amount:
                result = decimal.Decimal(0)
            else:
                result = self.pick_service_amount
        return result

    def get_delivery_amount_gross(self, delivery_method):
        """ 获取优惠前运费 """
        if delivery_method == OrderDeliveryMethod.HOME_DELIVERY:
            result = self.home_delivery_amount
        else:
            result = self.pick_service_amount
        return result

    def is_delivery_method_valid(self, delivery_method):
        """ 检查配送方式是由有效 """
        if (
            delivery_method == OrderDeliveryMethod.HOME_DELIVERY and not self.home_on
        ) or (
            delivery_method == OrderDeliveryMethod.CUSTOMER_PICK and not self.pick_on
        ):
            return False
        return True


class PickPeriodConfigLine(models.Model, TimeBaseMixin):
    """自提时间段模型类"""

    delivery_config = models.ForeignKey(
        DeliveryConfig,
        null=False,
        on_delete=models.CASCADE,
        verbose_name="订单配送配置对象"
    )
    from_time = models.CharField(max_length=16, null=False, verbose_name="自提起始时间")
    to_time = models.CharField(max_length=16, null=False, verbose_name="自提终止时间")

    class Meta:
        db_table = "pick_period_config_line"
        verbose_name = "自提时间段"
        verbose_name_plural = verbose_name





