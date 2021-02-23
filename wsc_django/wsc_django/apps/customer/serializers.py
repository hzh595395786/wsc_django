from rest_framework import serializers

from wsc_django.utils.setup import ConvertDecimalPlacesField
from user.serializers import UserSerializer

class AdminCustomerSerializer(serializers.Serializer):
    """后台用户详情序列化器类"""

    customer_id = serializers.IntegerField(source="id", label="客户id")
    consume_amount = ConvertDecimalPlacesField(max_digits=13, decimal_places=4, label="客户消费金额")
    consume_count = serializers.IntegerField(label="客户消费次数")
    point = ConvertDecimalPlacesField(max_digits=13, decimal_places=4, label="客户积分")
    remark = serializers.CharField(label="客户备注")
    customer_personal_data = UserSerializer(read_only=True, label="客户个人信息")
