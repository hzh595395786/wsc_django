from django.db import models

# Create your models here.
from product.models import Product
from shop.models import Shop
from user.models import User
from wsc_django.utils.models import TimeBaseMixin


class ProductBrowseRecord(models.Model, TimeBaseMixin):
    """货品访问记录模型类"""

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=False, verbose_name="对应的店铺对象")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, verbose_name="对应的用户对象")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, verbose_name="对应货品对象")
    start_time = models.DateTimeField(null=False, verbose_name="开始浏览时间")
    duration = models.IntegerField(null=False, verbose_name="停留时间")
    pre_page_name = models.CharField(max_length=32, verbose_name="上一页名称")
    next_page_name = models.CharField(max_length=32, verbose_name="下一页名称")

    class Meta:
        db_table = "prodoct_browse_record"
        verbose_name = "货品访问记录"
        verbose_name_plural = verbose_name
