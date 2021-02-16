from django_redis import get_redis_connection
from rest_framework import serializers

from staff.models import Staff, StaffApply
from staff.services import create_staff_apply
from user.serializers import UserSerializer
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.validators import mobile_validator


class StaffDetailSerializer(serializers.ModelSerializer):
    """员工序列化器类"""

    class Meta:
        model = Staff


class StaffApplyDetailSerializer(serializers.Serializer):
    """员工申请详情序列化器类"""
    id = serializers.IntegerField(read_only=True, label="员工申请id")
    status = serializers.IntegerField(label="申请状态")
    create_time = serializers.DateTimeField(required=False, source="create_at", format=DateFormat.TIME, label="员工申请创建时间")
    user_info = UserSerializer(label="用户信息")


class StaffApplyCreateSerializer(serializers.Serializer):
    """员工申请验证相关序列化器类"""
    realname = serializers.CharField(write_only=True, max_length=64, min_length=1, required=True, label="真实姓名")
    phone = serializers.CharField(
        write_only=True, required=True, min_length=11, max_length=11, validators=[mobile_validator], label="手机号"
    )
    sms_code = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4, label="短信验证码")
    birthday = serializers.DateField(write_only=True, required=False, label="生日")

    def validate(self, attrs):
        user = self.context["request"].user
        sms_code = attrs.pop("sms_code")
        phone = attrs["phone"]
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get("sms_%s_%s" % (user.id, phone))
        if not real_sms_code:
            raise serializers.ValidationError("无效的验证码")
        real_sms_code = real_sms_code.decode()
        if sms_code != real_sms_code:
            raise serializers.ValidationError("短信验证码不正确")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        shop = self.context["request"].shop
        user.realname = validated_data.pop("realname")
        user.phone = validated_data.pop("phone")
        if validated_data.get("birthday"):
            user.birthday = validated_data.pop("birthday")
        user.save()
        data = {"shop_id":shop.id, "user_id":user.id}
        staff = create_staff_apply(data)
        return staff