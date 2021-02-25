from django.db import models


class TimeBaseModel(models.Model):
    """ 标识字段，不参与任何业务，不增加索引 """

    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True  # 说明是抽象模型类, 用于继承使用，数据库迁移时不会创建TimeBaseModel的表
