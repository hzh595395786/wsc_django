from rest_framework import serializers

from user.serializers import UserSerializer
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.core import FuncField


class AdminProductStorageRecordsSerializer(serializers.Serializer):
    """后台货品库存变更记录序列化器类"""

    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="创建时间")
    type = serializers.IntegerField(label="变更类型")
    type_text = serializers.CharField(allow_blank=True, label="变更类型文字版")
    operator_type = serializers.IntegerField(label="操作人类型")
    operator = UserSerializer(source="user",label="操作人")
    change_storage = FuncField(lambda value: round(float(value)), label="变更量")
    current_storage = FuncField(lambda value: round(float(value)), label="当前量")
    order_num = serializers.CharField(default="-", label="订单号")
