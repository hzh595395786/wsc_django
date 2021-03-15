from rest_framework import serializers


class AdminDeliverySerializer(serializers.Serializer):
    """后台配送记录序列化器类"""

    delivery_type = serializers.IntegerField(label="配送方式")
    company = serializers.CharField(label="快递公司")
    express_num = serializers.CharField(label="快递单号")