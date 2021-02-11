from django.db import models

# Create your models here.
from product.models import Product
from shop.models import Shop
from user.models import User
from wsc_django.utils.models import TimeBaseMixin
from storage.constant import (
    ProductStorageRecordOperatorType,
    ProductStorageRecordType,
    ProductStorageRecordStatus,
)


class ProductStorageRecord(models.Model, TimeBaseMixin):
    """货品库存变更记录"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="对应的店铺对象")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, verbose_name="对应货品对象")
    operator_type = models.SmallIntegerField(
        null=False,
        default=ProductStorageRecordOperatorType.STAFF,
        verbose_name="操作人类型,1:员工,2:客户",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="对应的用户对象")
    create_time = models.DateTimeField(null=False, verbose_name="货品库存变更记录创建时间")
    type = models.SmallIntegerField(
        null=False,
        default=ProductStorageRecordType.MALL_SALE,
        verbose_name="货品库存记录变更类型",
    )
    change_storage = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="本次操作变更量",
    )
    current_storage = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        verbose_name="历史时刻当前库存",
    )
    order_num = models.CharField(max_length=20, verbose_name="订单号")
    status = models.SmallIntegerField(
        null=False,
        default=ProductStorageRecordStatus.NORMAL,
        verbose_name="状态"
    )

    class Meta:
        db_table = "prodoct_storage_record"
        verbose_name = "货品库存变更记录"
        verbose_name_plural = verbose_name

