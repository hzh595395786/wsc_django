from django.db import models

from groupon.constant import GrouponStatus
from product.models import Product
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
        null=False, default=24, verbose_name="开团有效时间(超过次时间未成团的活动将自动解散)"
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