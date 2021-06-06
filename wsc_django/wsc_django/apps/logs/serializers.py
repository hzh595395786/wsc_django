from rest_framework import serializers

from wsc_django.utils.constant import DateFormat


class OperatorSerializer(serializers.Serializer):
    """操作人序列化器类"""

    operator_id = serializers.IntegerField(source="id", label="操作人ID(User_id)")
    realname = serializers.CharField(required=False, label="用户真实姓名")
    nickname = serializers.CharField(required=False, label="微信昵称")
    sex = serializers.IntegerField(required=False, label="性别")
    head_image_url = serializers.CharField(required=False, label="头像")


class _LogSerializer(serializers.Serializer):
    """公用日志-不对外开放"""

    operate_time = serializers.DateTimeField(format=DateFormat.TIME, label="操作时间")
    operate_module = serializers.IntegerField(label="所属板块ID")
    operate_type_text = serializers.CharField(label="操作类型文字版")
    operate_content = serializers.CharField(label="操作内容")
    operator = OperatorSerializer(label="操作人")


class OrderLogSerializer(_LogSerializer):
    """订单日志序列化器类"""

    order_num = serializers.CharField(label="订单号")
    old_value = serializers.CharField(required=False, label="旧值,从content取得")
    new_value = serializers.CharField(required=False, label="新值,从content取得")


class ConfigLogSerializer(_LogSerializer):
    """设置日志序列化器类"""


class ProductLogSerializer(_LogSerializer):
    """货品日志序列化器类"""


class PromotionLogSerializer(_LogSerializer):
    """货品日志序列化器类"""

