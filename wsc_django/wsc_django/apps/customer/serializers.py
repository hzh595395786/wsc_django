from rest_framework import serializers

from customer.constant import CUSTOMER_POINT_TYPE
from customer.services import create_mine_address, check_default_address
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.core import FuncField, FormatAddress
from user.serializers import UserSerializer


class AdminCustomerSerializer(UserSerializer):
    """后台客户序列化器类"""

    customer_id = serializers.IntegerField(source="id", label="客户id")
    consume_amount = FuncField(lambda value: round(float(value), 2), label="客户消费金额")
    consume_count = serializers.IntegerField(label="客户消费次数")
    point = FuncField(lambda value: round(float(value), 2), label="客户积分")
    remark = serializers.CharField(label="客户备注")
    realname = serializers.CharField(required=False, label="用户真实姓名")
    nickname = serializers.CharField(required=False, label="微信昵称")
    sex = serializers.IntegerField(required=False, label="性别")
    phone = serializers.CharField(required=False, label="手机号")
    birthday = serializers.DateField(required=False, format=DateFormat.DAY, default="", label="用户生日")
    head_image_url = serializers.CharField(required=False, label="头像")


class AdminCustomerPointsSerializer(serializers.Serializer):
    """后台客户积分序列化器类"""

    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="操作时间")
    type = FuncField(lambda value: CUSTOMER_POINT_TYPE.get(value), label="操作类型")
    point_change = FuncField(lambda value: round(float(value), 2), label="积分变更值")
    current_point = FuncField(lambda value: round(float(value), 2), label="当前积分")


class MallMineAddressSerializer(serializers.Serializer):
    """商城端我的地址序列化器类"""

    address_id = serializers.IntegerField(read_only=True, source="id", label="地址id")
    name = serializers.CharField(label="收货人姓名")
    sex = serializers.IntegerField(label="收货人性别")
    phone = serializers.IntegerField(label="收货人电话")
    province = serializers.IntegerField(label="省份编号")
    city = serializers.IntegerField(label="城市编号")
    county = serializers.IntegerField(label="区编号")
    address = serializers.CharField(label="详细地址")
    default = serializers.IntegerField(label="是否为默认地址")
    longitude = serializers.FloatField(required=False, label="经度")
    latitude = serializers.FloatField(required=False, label="纬度")

    def validate(self, attrs):
        """验证省市区编号是否合法"""
        province = attrs.get("province")
        city = attrs.get("city")
        county = attrs.get("county")
        res = FormatAddress.check_code([province, city, county])
        if not res:
            raise serializers.ValidationError("省市区编号不合法")
        return attrs

    def create(self, validated_data):
        user = self.context["self"].current_user
        shop = self.context["self"].current_shop
        if 'default' in validated_data.keys() and validated_data['default']:
            check_default_address(user.id, shop.id)
        mine_address = create_mine_address(validated_data, user.id, shop.id)
        return mine_address

    def update(self, instance, validated_data):
        user = self.context["self"].current_user
        shop = self.context["self"].current_shop
        if 'default' in validated_data.keys() and validated_data['default']:
            check_default_address(user.id, shop.id)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
