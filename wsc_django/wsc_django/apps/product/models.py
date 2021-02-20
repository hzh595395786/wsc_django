from django.db import models

# Create your models here.
from shop.models import Shop
from wsc_django.utils.models import TimeBaseMixin
from product.constant import (
    ProductStatus,
    ProductGroupDefault
)


class ProductGroup(models.Model, TimeBaseMixin):
    """商品分组模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="对应的店铺对象")
    name = models.CharField(max_length=32, null=False, verbose_name="商品分组名称")
    description = models.CharField(max_length=128, default="无", verbose_name="商品分组描述")
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,verbose_name="该商品分组的父级ID")
    sort = models.IntegerField(null=True, verbose_name="商品分组排序")
    level = models.SmallIntegerField(null=True, verbose_name="商品分组级别")
    default = models.SmallIntegerField(
        null=False,
        default=ProductGroupDefault.NO,
        verbose_name="是否为默认分组, 0:否,1:是",
    )

    class Meta:
        db_table = "prodoct_group"
        verbose_name = "货品分组"
        verbose_name_plural = verbose_name

    def set_default_sort(self):
        self.sort = self.id


class Product(models.Model, TimeBaseMixin):
    """货品模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="货品对应的店铺对象")
    name = models.CharField(max_length=64, null=False, verbose_name="货品名称")
    name_acronym = models.CharField(max_length=64, null=False, verbose_name="货品名称拼音")
    group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, verbose_name="货品分组ID")
    price = models.DecimalField(max_digits=13, decimal_places=4, null=False, verbose_name="货品单价")
    storage = models.DecimalField(
        max_digits=13,
        decimal_places=4,
        null=False,
        default=0,
        verbose_name="货品库存"
    )
    code = models.CharField(max_length=32, default="", verbose_name="货品编码")
    summary = models.CharField(max_length=128, default="", verbose_name="货品简介")
    cover_image_url = models.CharField(max_length=512, default="", verbose_name="货品封面图")
    description = models.TextField(default="", verbose_name="货品详情描述")
    status = models.SmallIntegerField(
        null=False,
        default=ProductStatus.ON,
        verbose_name="货品状态, 0:删除, 1:上架, 2:下架",
    )

    class Meta:
        db_table = "prodoct"
        verbose_name = "货品"
        verbose_name_plural = verbose_name


class ProductPicture(models.Model, TimeBaseMixin):
    """货品轮播图模型类"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, verbose_name="对应货品对象")
    image_url = models.CharField(max_length=512, verbose_name="货品轮播图url")

    class Meta:
        db_table = "prodoct_picture"
        verbose_name = "货品轮播图"
        verbose_name_plural = verbose_name

