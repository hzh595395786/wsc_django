from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
from wsc_django.utils.models import TimeBaseMixin
from user.constant import (
    Sex
)


class User(AbstractUser, TimeBaseMixin):
    """用户模型类"""

    phone = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    password = models.CharField(max_length=128, verbose_name="密码（密文）")
    wx_unionid = models.CharField(max_length=64, verbose_name="微信unionid")
    sex = models.SmallIntegerField(
        null=True,
        default=Sex.UNKNOWN,
        verbose_name="用户性别 0:未知 1:男 2:女",
    )
    nickname = models.CharField(max_length=64, default="", verbose_name="用户昵称")
    realname = models.CharField(max_length=64, verbose_name="用户真姓名")
    birthday = models.DateField(verbose_name="生日")
    head_image_url = models.CharField(max_length=1024, verbose_name="用户头像URL")
    wx_openid = models.CharField(max_length=64, verbose_name="微信openid")
    wx_country = models.CharField(max_length=32, verbose_name="用户所在国家")
    wx_province = models.CharField(max_length=32, verbose_name="用户所在省份")
    wx_city = models.CharField(max_length=32, verbose_name="用户所在城市")

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(name="ux_phone", fields=["phone"]),
            models.Index(name="ux_wx_unionid", fields=["wx_unionid"])
        ]


# class UserOpenid(models.Model, TimeBaseMixin):
#     """用户openid与appid的对应关系"""
#
#     user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, verbose_name="对应的用户对象")
#     wx_openid = models.CharField(max_length=64, null=False, verbose_name="用户在对应公众号的openid")
#
#     def set_wx_openid(self, wx_openid):
#         """设置wx_openid"""
#         self.wx_openid = wx_openid