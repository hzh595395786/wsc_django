from django.db import models

from user.models import User
from shop.constant import (
    ShopStatus,
    ShopVerifyActive,
    ShopVerifyType,
    ShopPayActive,
)
from wsc_django.utils.models import TimeBaseModel


class Shop(TimeBaseModel):
    """商铺模型类"""

    status = models.SmallIntegerField(
        null=False,
        default=ShopStatus.CHECKING,
        verbose_name="商铺状态 0: 已关闭 1: 正常,审核通过, 2: 审核中, 3: 已拒绝",
    )
    super_admin = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="商铺老板")
    shop_name = models.CharField(max_length=128, null=False, verbose_name="商铺名称")
    shop_code = models.CharField(max_length=16, null=False, default="", verbose_name="随机字符串，用于代替id")
    shop_phone = models.CharField(max_length=32, null=False, default="", verbose_name="联系电话")
    shop_img = models.CharField(max_length=300, null=False, default="", verbose_name="门头照片")
    business_licence = models.CharField(max_length=300, null=False, default="", verbose_name="营业执照")
    shop_address = models.CharField(max_length=100, null=False, default="", verbose_name="商铺地址")
    shop_county = models.IntegerField(null=False, default=0, verbose_name="商铺所在国家编号")
    shop_province = models.IntegerField(null=False, default=0, verbose_name="商铺所在省份编号")
    shop_city = models.IntegerField(null=False, default=0, verbose_name="商铺所在城市编号")
    create_time = models.DateTimeField(null=False, auto_now_add=True, verbose_name="商铺创建时间")
    description = models.CharField(max_length=256, null=False, default="", verbose_name="商铺描述")
    inviter_phone = models.CharField(max_length=32, null=False, default="", verbose_name="推荐人手机号")
    cerify_active = models.SmallIntegerField(
        null=False,
        default=ShopVerifyActive.YES,
        verbose_name="是否认证,1:是,0:否"
    )
    shop_verify_type = models.SmallIntegerField(
        null=False,
        default=ShopVerifyType.INDIVIDUAL,
        verbose_name="商铺类型,0:企业,1:个人",
    )
    shop_verify_content = models.CharField(max_length=200, verbose_name="认证内容(公司名称)")
    pay_active = models.SmallIntegerField(
        null=False,
        default=ShopPayActive.YES,
        verbose_name="是否开通线上支付,1:是,0:否",
    )

    class Meta:
        db_table = "shop"
        verbose_name = "商铺"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(name="ux_shop_code", fields=["shop_code"]),
            models.Index(name="ix_super_admin", fields=["super_admin"]),
        ]


class HistoryRealName(TimeBaseModel):
    """存储店铺创建者的历史真实姓名"""

    id = models.OneToOneField(
        Shop, on_delete=models.CASCADE, primary_key=True, unique=True, null=False,verbose_name="对应的店铺id"
    )
    realname = models.CharField(max_length=32, null=False, verbose_name='历史真实姓名')

    class Meta:
        db_table = "history_realname"
        verbose_name = "商铺创建者历史真实姓名"
        verbose_name_plural = verbose_name


class ShopRejectReason(TimeBaseModel):
    """拒绝的商铺的拒绝理由"""

    id = models.OneToOneField(
        Shop, on_delete=models.CASCADE, primary_key=True, unique=True, null=False, verbose_name="对应的店铺id"
    )
    reject_reason = models.CharField(max_length=256, null=False, default='', verbose_name="拒绝理由")

    class Meta:
        db_table = "shop_reject_reason"
        verbose_name = "商铺拒绝理由"
        verbose_name_plural = verbose_name