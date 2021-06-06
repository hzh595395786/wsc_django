from rest_framework import serializers

from user.models import User
from user.services import create_user
from wsc_django.utils.constant import DateFormat


class UserCreateSerializer(serializers.Serializer):
    """创建用户序列化器类"""

    username = serializers.CharField(required=True, label="用户名，jwt必须")
    phone = serializers.CharField(required=True, label="手机号")
    password = serializers.CharField(required=False, label="密码")
    wx_unionid = serializers.CharField(required=False, max_length=64, label="微信unionid")
    sex = serializers.IntegerField(required=False, label="用户性别 0:未知 1:男 2:女")
    nickname = serializers.CharField(required=True, max_length=64, label="用户昵称")
    realname = serializers.CharField(required=False, max_length=64, label="用户真姓名")
    birthday = serializers.DateField(required=False, label="用户生日")
    head_image_url = serializers.CharField(required=True, max_length=1024, label="用户头像URL(存完整的)")
    wx_openid = serializers.CharField(required=False, max_length=64, label="微信openid")
    wx_country = serializers.CharField(required=False, max_length=32, label="用户所在国家")
    wx_province = serializers.CharField(required=False, max_length=32, label="用户所在省份")
    wx_city = serializers.CharField(required=False, max_length=32, label="用户所在城市")

    def create(self, validated_data):
        user = create_user(validated_data)
        return user


class UserSerializer(serializers.Serializer):
    """用户序列化器类"""

    realname = serializers.CharField(required=False, label="用户真实姓名")
    nickname = serializers.CharField(required=False, label="微信昵称")
    sex = serializers.IntegerField(required=False, label="性别")
    phone = serializers.CharField(required=False, label="手机号")
    birthday = serializers.DateField(required=False, format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(required=False, label="头像")


class operatorSerializer(serializers.Serializer):
    """审核操作人序列化器类"""

    operate_id = serializers.IntegerField(label="操作人id")
    operate_name = serializers.CharField(label="操作人名称")
    operate_img = serializers.CharField(label="操作人头像")


class SuperUserSerializer(UserSerializer):
    """总后台用户详情序列化器类"""

    user_id = serializers.IntegerField(source="id", label="用户id")
    username = serializers.CharField(label="用户名")
    email_active = serializers.BooleanField(label="是否激活邮箱")
    email = serializers.EmailField(label="邮箱")


class EmailSerializer(serializers.ModelSerializer):
    """用户邮箱序列化器类"""

    class Meta:
        model = User
        fields = ('id', 'email')

    def update(self, instance, validated_data):
        email = validated_data['email']
        instance.email = email
        instance.save()
        return instance