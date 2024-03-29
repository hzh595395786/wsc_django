from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData

from user.constant import Sex, VERIFY_EMAIL_TOKEN_EXPIRES
from wsc_django.utils.models import TimeBaseModel


class User(AbstractUser):
    """用户模型类"""

    phone = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email = models.EmailField(unique=True, max_length=254, null=True, verbose_name="邮箱")
    password = models.CharField(null=True, max_length=128, verbose_name="密码（密文）")
    wx_unionid = models.CharField(max_length=64, null=True, verbose_name="微信unionid")
    sex = models.SmallIntegerField(
        null=True,
        default=Sex.UNKNOWN,
        verbose_name="用户性别 0:未知 1:男 2:女",
    )
    nickname = models.CharField(max_length=64, default="", verbose_name="用户昵称")
    realname = models.CharField(max_length=64, default="",verbose_name="用户真姓名")
    birthday = models.DateField(null=True, verbose_name="用户生日")
    head_image_url = models.CharField(max_length=1024, verbose_name="用户头像URL(存完整的)")
    wx_openid = models.CharField(null=True, max_length=64, verbose_name="微信openid")
    wx_country = models.CharField(null=True, max_length=32, verbose_name="用户所在国家")
    wx_province = models.CharField(null=True, max_length=32, verbose_name="用户所在省份")
    wx_city = models.CharField(null=True, max_length=32, verbose_name="用户所在城市")
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(name="ux_phone", fields=["phone"]),
            models.Index(name="ux_wx_unionid", fields=["wx_unionid"])
        ]

    def generate_verify_email_url(self):
        """
        生成验证邮箱的url
        """
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=VERIFY_EMAIL_TOKEN_EXPIRES)
        data = {'user_id': self.id, 'email': self.email}
        token = serializer.dumps(data).decode()
        if settings.DEBUG:
            verify_url = 'http://127.0.0.1:3030/#/email-verify?token=' + token
        else:
            verify_url = 'http://hzhst1314.cn/#/email-verify?token=' + token
        return verify_url

    @staticmethod
    def check_verify_email_token(token):
        serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=VERIFY_EMAIL_TOKEN_EXPIRES)
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            user_id = data['user_id']
            email = data['email']
            try:
                user = User.objects.get(id=user_id, email=email)
            except User.DoesNotExist:
                return None
            else:
                return user


class UserOpenid(TimeBaseModel):
    """用户openid与appid的对应关系"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="useropenid", null=False, verbose_name="对应的用户对象")
    wx_openid = models.CharField(max_length=64, null=False, verbose_name="用户在对应公众号的openid")
    mp_appid = models.CharField(max_length=64, null=False, verbose_name="公众号的appid（特殊的，对于利楚服务商支付，格式为lcwx-[shop_id]）")

    class Meta:
        db_table = "user_openid"
        verbose_name = "用户openid"
        verbose_name_plural = verbose_name

    def set_wx_openid(self, wx_openid):
        """设置wx_openid"""
        self.wx_openid = wx_openid
