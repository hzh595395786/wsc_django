from rest_framework import serializers

from user.models import User
from user.services import create_user, create_user_openid
from wsc_django.utils.constant import DateFormat


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户序列化器类"""

    class Meta:
        model = User

    def create(self, validated_data):
        user = create_user(validated_data)
        self.context['request'].user = user
        return user


class UserOpenidSerializer(serializers.Serializer):
    """用户openid序列化器类"""

    user_id = serializers.IntegerField(label="用户id")
    mp_appid = serializers.CharField(label="公众号appid")
    wx_openid = serializers.CharField(label="用户openid")

    def create(self, validated_data):
        user_openid = create_user_openid(**validated_data)
        return user_openid


class UserSerializer(serializers.Serializer):
    """用户序列化器类"""

    realname = serializers.CharField(label="用户真实姓名")
    nickname = serializers.CharField(label="微信昵称")
    sex = serializers.IntegerField(label="性别")
    phone = serializers.CharField(label="手机号")
    birthday = serializers.DateField(format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(label="头像")