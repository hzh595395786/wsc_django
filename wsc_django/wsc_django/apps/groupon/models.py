import datetime
import decimal

from django.db import models

from customer.models import Customer
from groupon.constant import GrouponStatus, GrouponAttendStatus, GrouponType, GrouponAttendLineStatus
from product.models import Product
from promotion.abstract import AbstractPromotionRule
from shop.models import Shop
from wsc_django.utils.models import TimeBaseModel


class Groupon(TimeBaseModel):
    """拼团活动模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="对应的店铺对象")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, verbose_name="对应的货品对象")
    price = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="商品拼团价格")
    from_datetime = models.DateTimeField(null=False, verbose_name="拼团活动开始时间")
    to_datetime = models.DateTimeField(null=False, verbose_name="拼团活动结束时间")
    groupon_type = models.SmallIntegerField(null=False, verbose_name="拼团活动类型 1:普通 2:老带新")
    success_size = models.SmallIntegerField(null=False, default=1, verbose_name="成团人数")
    quantity_limit = models.IntegerField(
        null=False, default=0, verbose_name="购买数量上限（限制每个订单的购买数量）"
    )
    success_limit = models.IntegerField(
        null=False, default=0, verbose_name="成团数量上限(限制单次活动的最大成团数量)"
    )
    attend_limit = models.IntegerField(
        null=False, default=0, verbose_name="参团数量上限(每个用户能参加同一拼团的次数)"
    )
    success_valid_hour = models.IntegerField(
        null=False, default=24, verbose_name="开团有效时间(超过此时间未成团的活动将自动解散)"
    )
    status = models.SmallIntegerField(
        null=False, default=GrouponStatus.ON, verbose_name="拼团活动状态 1:启用 2:停用 3:过期"
    )
    succeeded_count = models.IntegerField(null=False, default=0, verbose_name="成团数")
    succeeded_quantity = models.DecimalField(
        max_digits=13, decimal_places=4, null=False, default=0, verbose_name="成团件数"
    )
    is_editable = models.BooleanField(null=False, default=True, verbose_name="是否可以编辑")

    class Meta:
        db_table = "groupon"
        verbose_name = "拼团活动"
        verbose_name_plural = verbose_name

    def set_expired(self):
        self.status = GrouponStatus.EXPIRED

    def set_uneditable(self):
        self.is_editable = False


class GrouponAttend(TimeBaseModel, AbstractPromotionRule):
    """拼团参与表"""

    groupon = models.ForeignKey(Groupon, null=False, on_delete=models.CASCADE, verbose_name="拼团活动")
    size = models.IntegerField(null=False, default=0, verbose_name="拼团当前参与人数")
    anonymous_size = models.IntegerField(null=False, default=0, verbose_name="强制成团添加的匿名用户数量")
    success_size = models.IntegerField(null=False, verbose_name="成团人数")
    to_datetime = models.DateTimeField(null=False, verbose_name="拼团参与结束时间")
    status = models.SmallIntegerField(
        null=False,
        default=GrouponAttendStatus.CREATED,
        verbose_name="拼团参与状态 -1: 超时未支付 0:已创建 1:拼团中 2:已成团 3:已失败"
    )
    failed_reason = models.CharField(max_length=64, null=False, default="", verbose_name="失败原因")

    class Meta:
        db_table = "groupon_attend"
        verbose_name = "拼团参与表"
        verbose_name_plural = verbose_name

    def is_sponsor(self, customer) -> bool:
        """ 客户是否是团长 """
        return customer.id == self.sponsor_detail.customer_id

    def calculate(self) -> decimal.Decimal:
        """ 拼团价格优惠计算, 返回优惠后的价格 """
        return self.groupon.price

    def set_succeeded(self):
        self.status = GrouponAttendStatus.SUCCEEDED

    def set_failed(self, reason: str):
        self.status = GrouponAttendStatus.FAILED
        self.failed_reason = reason

    def limit(self, customer, quantity_net) -> tuple:
        """开团、参团过程中的校验"""
        if self.size + 1 > self.success_size:
            return False, "本团已满员, 去看看其他团吧"
        if (
            self.groupon.to_datetime <= datetime.datetime.now()
            or self.groupon.status != GrouponStatus.ON
        ):
            return False, "活动已结束, 看看其他商品吧"
        # 团长支付后才倒计时, 团长不做过期验证, 活动过期在上面有验证,会被拦截
        if (not self.is_sponsor(customer)) and (
            self.to_datetime <= datetime.datetime.now()
            or (self.status != GrouponAttendStatus.WAITTING)
        ):
            return False, "本团已过期,去看看其他团吧"
        if (
            self.groupon.success_limit
            and self.groupon.succeeded_count >= self.groupon.success_limit
        ):
            return False, "成团数已达到上限, 去参加其他团吧"
        if (
            self.groupon.groupon_type == GrouponType.MENTOR
            and not customer.is_new_customer()
            and not self.is_sponsor(customer)
        ):
            return False, "邀新团仅允许新用户参与"
        if self.groupon.quantity_limit and quantity_net > self.groupon.quantity_limit:
            return (
                False,
                "本团限购{quantity_limit}, 请减少购买数量后再试".format(
                    quantity_limit=self.groupon.quantity_limit
                ),
            )
        # 是否已经参团判断
        attend_detail = (
            GrouponAttendDetail.objects.filter(
                groupon_attend_id=self.id,
                customer_id=customer.id,
                status__in=[GrouponAttendLineStatus.PAID, GrouponAttendLineStatus.UNPAID],
            )
            .first()
        )
        if attend_detail and not self.is_sponsor(customer):
            return False, "您已经参加过该团"
        # 参团数量限制
        if self.groupon.attend_limit:
            total_attend_count = (
                GrouponAttendDetail.objects.filter(
                    groupon_attend__groupon_id=self.groupon.id,
                    groupon_attend__groupon_status__in=[GrouponAttendStatus.WAITTING, GrouponAttendStatus.SUCCEEDED],
                    customer_id=customer.id,
                    status__in=[GrouponAttendLineStatus.PAID, GrouponAttendLineStatus.UNPAID]
                )
                .count()
            )
            if total_attend_count >= self.groupon.attend_limit:
                return (
                    False,
                    "最多参加{attend_limit}次, 您已达到上限".format(
                        attend_limit=self.groupon.attend_limit
                    ),
                )
        return True, ""


class GrouponAttendDetail(TimeBaseModel):
    """拼团参与详情表"""

    groupon_attend = models.ForeignKey(
        GrouponAttend, on_delete=models.CASCADE, null=False, verbose_name="拼团参与"
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=False, verbose_name="参与客户")
    is_sponsor = models.BooleanField(null=False, default=True, verbose_name="是否是团长")
    is_new_customer = models.BooleanField(null=False, default=False, verbose_name="是否是新用户")
    status = models.SmallIntegerField(
        null=False, default=GrouponAttendLineStatus.UNPAID, verbose_name="参团状态 -1:超时未支付 0:未支付 1:已支付"
    )

    class Meta:
        db_table = "groupon_attend_detail"
        verbose_name = "拼团参与详情表"
        verbose_name_plural = verbose_name