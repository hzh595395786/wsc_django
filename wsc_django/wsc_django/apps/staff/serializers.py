from django_redis import get_redis_connection
from rest_framework import serializers

from staff.constant import StaffApplyStatus, StaffRole
from staff.services import create_staff_apply, create_staff
from user.serializers import UserSerializer
from wsc_django.utils.constant import DateFormat


class StaffSerializer(serializers.Serializer):
    """员工序列化器类"""

    staff_id = serializers.IntegerField(read_only=True, source="id", label="员工id")
    roles = serializers.IntegerField(required=True, label="角色")
    permissions = serializers.IntegerField(required=True, label="权限")
    position = serializers.CharField(required=False, min_length=0, max_length=16, allow_null=True, label="员工职位")
    entry_date = serializers.DateField(required=False, format=DateFormat.DAY, allow_null=True, label="入职日期")
    remark = serializers.CharField(required=False, min_length=0, max_length=20, allow_null=True, label="备注")
    shop_id = serializers.IntegerField(write_only=True, required=False, label="商铺id，仅创建时使用")
    user_id = serializers.IntegerField(write_only=True, required=False, label="用户id，仅创建时使用")
    realname = serializers.CharField(read_only=True, label="用户真实姓名")
    nickname = serializers.CharField(read_only=True, label="微信昵称")
    sex = serializers.IntegerField(read_only=True, label="性别")
    phone = serializers.CharField(read_only=True, label="手机号")
    birthday = serializers.DateField(read_only=True, format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(read_only=True, label="头像")

    def create(self, validated_data):
        staff = create_staff(validated_data)
        return staff

    def update(self, instance, validated_data):
        # 超管不可编辑权限和角色
        if instance.roles == StaffRole.SHOP_SUPER_ADMIN:
            validated_data.pop("roles", 0)
            validated_data.pop("permissions", 0)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class StaffApplySerializer(serializers.Serializer):
    """员工申请序列化器类"""

    staff_apply_id = serializers.IntegerField(source="id", read_only=True, label="员工申请id")
    status = serializers.IntegerField(read_only=True, label="申请状态")
    create_time = serializers.DateTimeField(
        read_only=True, required=False, source="create_at", format=DateFormat.TIME, label="员工申请创建时间"
    )
    user_info = UserSerializer(source="user", read_only=True, label="用户信息")

    def update(self, instance, validated_data):
        instance.status = StaffApplyStatus.PASS
        instance.save()
        return instance


class StaffApplyCreateSerializer(serializers.Serializer):
    """员工申请验证相关序列化器类"""

    realname = serializers.CharField(write_only=True, max_length=64, min_length=1, required=True, label="真实姓名")
    phone = serializers.CharField(
        write_only=True, required=True, min_length=11, max_length=11, label="手机号"
    )
    sms_code = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4, label="短信验证码")
    birthday = serializers.DateField(write_only=True, required=False, label="生日")

    def validate(self, attrs):
        user = self.context["self"].current_user
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
        user = self.context["self"].current_user
        shop = self.context["self"].current_shop
        user.realname = validated_data.pop("realname")
        user.phone = validated_data.pop("phone")
        if validated_data.get("birthday"):
            user.birthday = validated_data.pop("birthday")
        user.save()
        data = {"shop_id":shop.id, "user_id":user.id}
        staff = create_staff_apply(data)
        return staff