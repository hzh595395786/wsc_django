from rest_framework import serializers

from customer.constant import CUSTOMER_POINT_TYPE
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.core import FuncField
from user.serializers import UserSerializer


class AdminCustomerSerializer(serializers.Serializer):
    """后台客户序列化器类"""

    customer_id = serializers.IntegerField(source="id", label="客户id")
    consume_amount = FuncField(lambda value: round(float(value), 2), label="客户消费金额")
    consume_count = serializers.IntegerField(label="客户消费次数")
    point = FuncField(lambda value: round(float(value), 2), label="客户积分")
    remark = serializers.CharField(label="客户备注")
    customer_personal_data = UserSerializer(source='user', required=False, read_only=True, label="客户个人信息")


class AdminCustomerPointsSerializer(serializers.Serializer):
    """后台客户积分序列化器类"""

    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="操作时间")
    type = FuncField(lambda value: CUSTOMER_POINT_TYPE.get(value), label="操作类型")
    point_change = FuncField(lambda value: round(float(value), 2), label="积分变更值")
    current_point = FuncField(lambda value: round(float(value), 2), label="当前积分")
