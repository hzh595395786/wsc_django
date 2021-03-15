from django.db import models

from logs.constant import OperateLogModule, ORDER_LOG_TYPE
from shop.models import Shop
from wsc_django.utils.models import TimeBaseModel

class OrderLog(TimeBaseModel):
    """订单日志模型类"""

    order_num = models.CharField(max_length=20, null=False, verbose_name="订单号")
    order_id = models.IntegerField(null=False, verbose_name="订单id")
    shop_id = models.IntegerField(null=False, verbose_name="商铺id")
    operate_time = models.DateTimeField(auto_now_add=True, null=False, verbose_name="操作时间")
    operator_id = models.IntegerField(null=False, verbose_name="操作人的user_id")
    operate_type = models.SmallIntegerField(null=False, verbose_name="操作类型")
    operate_content = models.CharField(max_length=512, default="", verbose_name="操作内容")

    class Meta:
        db_table = "order_log"
        verbose_name = "订单日志"
        verbose_name_plural = verbose_name

    @property
    def operate_module(self):
        return OperateLogModule.ORDER

    @property
    def operate_type_text(self):
        return ORDER_LOG_TYPE.get(self.operate_type)
