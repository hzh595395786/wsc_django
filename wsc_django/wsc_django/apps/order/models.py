import datetime

from django.db import models

from customer.models import Customer
from delivery.models import Delivery
from groupon.models import GrouponAttend
from product.models import Product
from shop.models import Shop
from order.constant import (
    OrderDeliveryMethod,
    OrderStatus,
    OrderPayType,
    OrderType,
    OrderRefundType,
)
from user.constant import Sex
from wsc_django.utils.core import FormatAddress
from wsc_django.utils.models import TimeBaseModel


class Order(TimeBaseModel):
    """订单模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="订单对应的店铺对象")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False, verbose_name="订单对应客户对象")
    groupon_attend = models.ForeignKey(GrouponAttend, on_delete=models.CASCADE, null=True, verbose_name="订单对应拼团参与对象")
    create_date = models.DateField(null=False, auto_now_add=True, verbose_name="下单日期")
    create_time = models.DateTimeField(null=False, auto_now_add=True, verbose_name="下单时间")
    delivery = models.ForeignKey(Delivery, null=True, on_delete=models.CASCADE, verbose_name="订单对应配送记录对象")
    delivery_method = models.SmallIntegerField(
        null=False,
        default=OrderDeliveryMethod.HOME_DELIVERY,
        verbose_name="配送方式,1:送货上门,2:客户自提",
    )
    delivery_period = models.CharField(max_length=32, null=False, verbose_name="自提处理时段")
    order_num = models.CharField(max_length=20, null=False, unique=True, verbose_name="订单号")
    order_status = models.SmallIntegerField(
        null=False,
        default=OrderStatus.UNPAID,
        verbose_name="订单状态,具体见constant",
    )
    remark = models.CharField(max_length=64, default="", verbose_name="订单备注")
    pay_type = models.SmallIntegerField(
        null=False,
        default=OrderPayType.ON_DELIVERY,
        verbose_name="订单支付方式",
    )
    order_type = models.SmallIntegerField(
        null=False,
        default=OrderType.NORMAL,
        verbose_name="订单类型,1:普通订单，2：拼团订单",
    )
    amount_gross = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="货款金额（优惠前）"
    )
    amount_net = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="货款金额（优惠后）"
    )
    delivery_amount_gross = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="货款金额运费（优惠前）",
    )
    delivery_amount_net = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="货款金额运费（优惠后）",
    )
    total_amount_gross = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="订单金额（优惠前）"
    )
    total_amount_net = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="订单金额（优惠后）"
    )
    refund_type = models.SmallIntegerField(
        null=False,
        default=OrderRefundType.UNDERLINE_REFUND,
        verbose_name="订单退款方式",
    )

    class Meta:
        db_table = "order"
        verbose_name = "订单"
        verbose_name_plural = verbose_name

    def set_num(self, order_num: str):
        """设置订单号"""
        self.order_num = order_num

    @property
    def delivery_period_text(self):
        """返回一个配送详情"""
        if self.delivery_method == OrderDeliveryMethod.CUSTOMER_PICK:
            day, period = self.delivery_period.split(" ")
            if day == datetime.date.today().strftime("%Y-%m-%d"):
                result = "今天 {}".format(period)
            elif day == (datetime.date.today() + datetime.timedelta(1)).strftime(
                    "%Y-%m-%d"
            ):
                result = "明天 {}".format(period)
            else:
                result = self.delivery_period
        else:
            result = self.delivery_period
        return result

    @property
    def delivery_amount_text(self):
        """根据配送方式返回费用类型"""
        if self.delivery_method == OrderDeliveryMethod.HOME_DELIVERY:
            return "配送费"
        else:
            return "服务费"

    @property
    def pay_type_text(self):
        """返回付款类型"""
        if self.pay_type == OrderPayType.WEIXIN_JSAPI:
            return "微信支付"
        else:
            return "货到付款"


class OrderDetail(TimeBaseModel):
    """订单详情模型类"""

    order = models.ForeignKey(Order, related_name="order_detail",on_delete=models.CASCADE, null=False, verbose_name="对应的订单对象")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="对应的店铺对象")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, verbose_name="对应的货品对象")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False, verbose_name="订单对应客户对象")
    create_date = models.DateField(null=False, auto_now_add=True, verbose_name="下单日期")
    quantity_gross = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="量（优惠前）")
    quantity_net = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="量（优惠后）")
    price_gross = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="单价（优惠前）")
    price_net = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="单价（优惠后）")
    amount_gross = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="金额（优惠前）")
    amount_net = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="金额（优惠后）")
    status = models.SmallIntegerField(null=False, verbose_name="订单状态,同order")
    pay_type = models.SmallIntegerField(null=False, verbose_name="支付方式,同order")
    refund_type = models.SmallIntegerField(null=True, verbose_name="退款方式,同order")
    promotion_type = models.SmallIntegerField(
        null=False,
        default="",
        verbose_name="活动类型（预留）",
    )

    class Meta:
        db_table = "order_detail"
        verbose_name = "订单详情"
        verbose_name_plural = verbose_name


class OrderAddress(TimeBaseModel):
    """订单地址模型类"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, verbose_name="对应的订单对象")
    province = models.IntegerField(verbose_name="省份编码")
    city = models.IntegerField(verbose_name="城市编码")
    county = models.IntegerField(verbose_name="区编码")
    address = models.CharField(max_length=64, null=False, verbose_name="详细地址")
    name = models.CharField(max_length=32, null=False, verbose_name="收件人姓名")
    sex = models.SmallIntegerField(null=False, default=Sex.UNKNOWN, verbose_name="收件人性别,0:未知1:男2:女")
    phone = models.CharField(max_length=32, default="", verbose_name="收件人手机号")

    class Meta:
        db_table = "order_address"
        verbose_name = "订单地址"
        verbose_name_plural = verbose_name

    @property
    def full_address(self):
        return FormatAddress.get_format_address(
            self.province, self.city, self.county, self.address
        )

    @property
    def sex_text(self):
        if self.sex == Sex.MALE:
            result = "先生"
        elif self.sex == Sex.FEMALE:
            result = "女士"
        else:
            result = "未知"
        return result