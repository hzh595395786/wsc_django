from rest_framework import serializers

from user.serializers import UserSerializer
from wsc_django.utils.constant import DateFormat


class ProductBrowseRecordsSerializer(serializers.Serializer):
    """货品浏览记录列表"""

    start_time = serializers.DateTimeField(format=DateFormat.TIME, label="浏览时间")
    duration = serializers.IntegerField(label="停留时间")
    pre_page_name = serializers.CharField(label="上一页名称")
    next_page_name = serializers.CharField(label="下一页名称")
    user = UserSerializer(label="用户信息")