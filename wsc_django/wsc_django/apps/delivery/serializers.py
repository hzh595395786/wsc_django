from rest_framework import serializers

from wsc_django.utils.core import FuncField


class PickPeriodConfigLineSerializer(serializers.Serializer):
    """自提时间段序列化器类"""

    from_time = serializers.DateTimeField(label="自提起始时间")
    to_time = serializers.DateTimeField(label="自提终止时间")


class AdminDeliverySerializer(serializers.Serializer):
    """后台配送记录序列化器类"""

    delivery_type = serializers.IntegerField(label="配送方式")
    company = serializers.CharField(label="快递公司")
    express_num = serializers.CharField(label="快递单号")


class AdminDeliveryConfigSerializer(serializers.Serializer):
    """后台配送配置序列化器类"""

    home_on = serializers.BooleanField(label="配送模式是否开启")
    home_minimum_order_amount = FuncField(lambda value: round(float(value), 2), label="配送模式起送金额")
    home_delivery_amount = FuncField(lambda value: round(float(value), 2), label="配送模式配送费")
    home_minimum_free_amount = FuncField(lambda value: round(float(value), 2), label="配送模式免配送费最小金额")
    pick_on = serializers.BooleanField(label="自提模式是否开启")
    pick_service_amount = FuncField(lambda value: round(float(value), 2), label="自提模式服务费")
    pick_minimum_free_amount = FuncField(lambda value: round(float(value), 2), label="自提模式免服务费最小金额")
    pick_today_on = serializers.BooleanField(label="今天自提是否开启")
    pick_tomorrow_on = serializers.BooleanField(label="明天自提是否开启")
    pick_periods = PickPeriodConfigLineSerializer(many=True, label="自提时间段")