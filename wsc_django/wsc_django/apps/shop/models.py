from django.db import models

# Create your models here.
from user.models import User
from wsc_django.utils.models import TimeBaseMixin
from .constant import (
    ShopStatus,
    ShopVerifyActive,
    ShopVerifyType,
    ShopPayActive,
)


class Shop(models.Model, TimeBaseMixin):
    """店铺模型类"""

    status = models.SmallIntegerField(
        null=False,
        default=ShopStatus.CHECKING,
        verbose_name="店铺状态 0: 已关闭 1: 正常,审核通过, 2: 审核中, 3: 已拒绝",
    )
    super_admin = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="店铺老板")
    shop_name = models.CharField(max_length=128, null=False, verbose_name="店铺名称")
    shop_code = models.CharField(max_length=16, null=False, default="", verbose_name="随机字符串，用于代替id")
    shop_phone = models.CharField(max_length=32, null=False, default="", verbose_name="联系电话")
    shop_img = models.CharField(max_length=300, null=False, default="", verbose_name="门头照片")
    business_licence = models.CharField(max_length=300, null=False, default="", verbose_name="营业执照")
    shop_address = models.CharField(max_length=100, null=False, default="", verbose_name="店铺地址")
    shop_country = models.IntegerField(null=False, default=0, verbose_name="店铺所在国家")
    shop_province = models.IntegerField(null=False, default=0, verbose_name="店铺所在省份")
    shop_city = models.IntegerField(null=False, default=0, verbose_name="店铺所在城市")
    create_time = models.DateTimeField(null=False, auto_now_add=True, verbose_name="店铺创建时间")
    cerify_active = models.SmallIntegerField(
        null=False,
        default=ShopVerifyActive.YES,
        verbose_name="是否认证,1:是,0:否"
    )
    shop_verify_type = models.SmallIntegerField(
        null=False,
        default=ShopVerifyType.INDIVIDUAL,
        verbose_name="店铺类型,0:企业,1:个人",
    )
    shop_verify_content = models.CharField(max_length=200, verbose_name="认证内容(公司名称)")
    pay_active = models.SmallIntegerField(
        null=False,
        default=ShopPayActive.YES,
        verbose_name="是否开通线上支付,1:是,0:否",
    )
    longitude = models.DecimalField(max_digits=10, decimal_places=6, verbose_name="经度")
    latitude = models.DecimalField(max_digits=10, decimal_places=6, verbose_name="纬度")

    class Meta:
        db_table = "shop"
        verbose_name = "店铺"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(name="ux_shop_code", fields=["shop_code"]),
            models.Index(name="ix_super_admin", fields=["spuer_admin_id"]),
        ]