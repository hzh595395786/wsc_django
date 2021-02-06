from django.db import models

class TimeBaseMixin:
    """ 标识字段，不参与任何业务，不增加索引 """

    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True