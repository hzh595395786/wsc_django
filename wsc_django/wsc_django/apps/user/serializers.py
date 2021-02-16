from rest_framework import serializers

from wsc_django.utils.constant import DateFormat


class MallUserSerializer(serializers.Serializer):
    """商城端登录注册"""
    """
    登录或注册成功后，在request中设置当前用户
    """

    pass


class UserSerializer(serializers.Serializer):
    """用户序列化器类"""

    realname = serializers.CharField(label="用户真实姓名")
    nickname = serializers.CharField(label="微信昵称")
    sex = serializers.IntegerField(label="性别")
    phone = serializers.CharField(label="手机号")
    birthday = serializers.DateField(format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(label="头像")