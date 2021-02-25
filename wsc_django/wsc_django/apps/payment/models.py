from django.db import models

from order.models import Order
from wsc_django.utils.models import TimeBaseModel


class OrderTransaction(TimeBaseModel):
    """订单在线支付信息模型类"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=False, verbose_name="对应订单对象")
    receipt_fee = models.IntegerField(null=False, verbose_name="实际支付金额")
    transaction_id = models.CharField(max_length=64, null=False, verbose_name="支付交易单号")
    channel_trade_no = models.CharField(max_length=64, null=False, verbose_name="支付通道的支付单号")

    class Meta:
        db_table = "order_transaction"
        verbose_name = "订单在线支付信息"
        verbose_name_plural = verbose_name