from rest_framework import serializers

from user.models import User
from user.services import create_user
from wsc_django.utils.constant import DateFormat


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户序列化器类"""

    class Meta:
        model = User

    def create(self, validated_data):
        user = create_user(validated_data)
        self.context['request'].user = user
        return user


class UserSerializer(serializers.Serializer):
    """用户序列化器类"""

    realname = serializers.CharField(required=False, label="用户真实姓名")
    nickname = serializers.CharField(required=False, label="微信昵称")
    sex = serializers.IntegerField(required=False, label="性别")
    phone = serializers.CharField(label="手机号")
    birthday = serializers.DateField(required=False, format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(required=False, label="头像")


class operatorSerializer(serializers.Serializer):
    """审核操作人序列化器类"""

    operate_id = serializers.IntegerField(label="操作人id")
    operate_name = serializers.CharField(label="操作人名称")
    operate_img = serializers.CharField(label="操作人头像")