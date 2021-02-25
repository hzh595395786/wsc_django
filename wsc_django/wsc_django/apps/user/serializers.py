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

    realname = serializers.CharField(label="用户真实姓名")
    nickname = serializers.CharField(label="微信昵称")
    sex = serializers.IntegerField(label="性别")
    phone = serializers.CharField(label="手机号")
    birthday = serializers.DateField(format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(label="头像")


class operatorSerializer(serializers.Serializer):
    """审核操作人序列化器类"""

    operate_id = serializers.IntegerField(label="操作人id")
    operate_name = serializers.CharField(label="操作人名称")
    operate_img = serializers.CharField(label="操作人头像")