from django.db import models

from logs.constant import OperateLogModule, ORDER_LOG_TYPE, CONFIG_LOG_TYPE, PROMOTION_LOG_TYPE
from user.models import User
from wsc_django.utils.models import TimeBaseModel


class OperateLogUnify(TimeBaseModel):
    """操作记录模型类"""

    shop_id = models.IntegerField(null=False, verbose_name="商铺id")
    operator = models.ForeignKey(
        User, null=False, on_delete=models.CASCADE, db_constraint=False, verbose_name="操作人"
    )
    operate_time = models.DateTimeField(auto_now_add=True, null=False, verbose_name="操作时间")
    operate_module = models.SmallIntegerField(null=False, verbose_name="操作模块")
    log_id = models.IntegerField(null=False, verbose_name="子模块的操作记录id")

    class Meta:
        db_table = "operate_log_unify"
        verbose_name = "操作记录"
        verbose_name_plural = verbose_name

    @classmethod
    def get_operate_log_model(cls, module_id):
        return {
            OperateLogModule.CONFIG: ConfigLog,
            OperateLogModule.ORDER: OrderLog,
            # OperateLogModule.STAFF: StaffLog,
            # OperateLogModule.PRODUCT: ProductLog,
            # OperateLogModule.PROMOTION: PromotionLog,
        }.get(module_id)


class OrderLog(TimeBaseModel):
    """订单日志模型类"""

    order_num = models.CharField(max_length=20, null=False, verbose_name="订单号")
    order_id = models.IntegerField(null=False, verbose_name="订单id")
    shop_id = models.IntegerField(null=False, verbose_name="商铺id")
    operate_time = models.DateTimeField(auto_now_add=True, null=False, verbose_name="操作时间")
    operator = models.ForeignKey(
        User, null=False, on_delete=models.CASCADE, db_constraint=False, verbose_name="操作人"
    )
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


class ConfigLog(TimeBaseModel):
    """设置模块操作日志模型类"""

    shop_id = models.IntegerField(null=False, verbose_name="商铺id")
    operate_time = models.DateTimeField(auto_now_add=True, null=False, verbose_name="操作时间")
    operator = models.ForeignKey(
        User, null=False, on_delete=models.CASCADE, db_constraint=False, verbose_name="操作人"
    )
    operate_type = models.SmallIntegerField(null=False, verbose_name="操作类型")
    operate_content = models.CharField(max_length=512, default="", verbose_name="操作内容")

    class Meta:
        db_table = "config_log"
        verbose_name = "设置模块操作日志"
        verbose_name_plural = verbose_name

    @property
    def operate_module(self):
        return OperateLogModule.CONFIG

    @property
    def operate_type_text(self):
        return CONFIG_LOG_TYPE.get(self.operate_type)


class PromotionLog(TimeBaseModel):
    """玩法日志模型类"""

    shop_id = models.IntegerField(null=False, verbose_name="商铺id")
    operate_time = models.DateTimeField(auto_now_add=True, null=False, verbose_name="操作时间")
    operator = models.ForeignKey(
        User, null=False, on_delete=models.CASCADE, db_constraint=False, verbose_name="操作人"
    )
    operate_type = models.SmallIntegerField(null=False, verbose_name="操作类型")
    operate_content = models.CharField(max_length=512, default="", verbose_name="操作内容")

    class Meta:
        db_table = "promotion_log"
        verbose_name = "玩法日志"
        verbose_name_plural = verbose_name

    @property
    def operate_module(self):
        return OperateLogModule.PROMOTION

    @property
    def operate_type_text(self):
        return PROMOTION_LOG_TYPE.get(self.operate_type)