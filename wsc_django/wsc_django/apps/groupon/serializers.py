from rest_framework import serializers

from groupon.services import create_groupon, update_groupon
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.core import FuncField


class AdminGrouponCreateSerializer(serializers.Serializer):
    """后台拼团活动创建序列化器"""

    price = FuncField(lambda value: round(float(value), 2), label="拼团价格")
    from_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动开始时间")
    to_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动结束时间")
    groupon_type = serializers.IntegerField(label="拼团活动类型 1:普通 2:老带新")
    success_size = serializers.IntegerField(label="成团人数")
    quantity_limit = serializers.IntegerField(label="成团数量上限")
    success_limit = serializers.IntegerField(label="成团上限")
    attend_limit = serializers.IntegerField(label="参团上限")
    success_valid_hour = serializers.IntegerField(label="开团有效时间")

    def create(self, validated_data):
        shop_id = self.context["self"].current_shop.id
        user_id = self.context["self"].current_user.id
        product = self.context["product"]
        groupon = create_groupon(
            shop_id, user_id, product, validated_data
        )
        return groupon

    def update(self, instance, validated_data):
        shop_id = self.context["self"].current_shop.id
        user_id = self.context["self"].current_user.id
        product = self.context["product"]
        instance = update_groupon(
            shop_id, user_id, product, instance, validated_data
        )
        return instance


class SponsorSerializer(serializers.Serializer):
    """团长信息，只需基本信息，所以新建一个序列化器"""

    nickname = serializers.CharField(required=False, label="微信昵称")
    sex = serializers.IntegerField(required=False, label="性别")
    head_image_url = serializers.CharField(required=False, label="头像")


class GrouponBasicSerializer(serializers.Serializer):
    """拼团活动基本信息序列化器类"""

    groupon_type = serializers.IntegerField(label="拼团活动类型 1:普通 2:老带新")
    success_valid_hour = serializers.IntegerField(label="开团有效时间")
    succeeded_count = serializers.IntegerField(label="成团数")
    success_limit = serializers.IntegerField(label="成团上限")


class GrouponProductSerializer(serializers.Serializer):
    """拼团商品序列化器类"""

    product_id = serializers.IntegerField(source="id", label="货品ID")
    name = serializers.CharField(label="货品名称")
    price = FuncField(lambda value: round(float(value), 2), label="货品价格")
    status = serializers.IntegerField(read_only=True, label="货品状态")
    summary = serializers.CharField(label="货品简介")
    cover_image_url = serializers.CharField(label="货品封面图")


class AdminGrouponsSerializer(GrouponBasicSerializer):
    """后台拼团活动列表序列化器类"""

    groupon_id = serializers.IntegerField(source="id", label="拼团id")
    product = GrouponProductSerializer(label="拼团商品信息")
    price = FuncField(lambda value: round(float(value), 2), label="拼团价格")
    attend_limit = serializers.IntegerField(label="参团上限")
    from_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动开始时间")
    to_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动结束时间")
    status = serializers.IntegerField(label="拼团活动状态 1:启用 2:停用 3:过期")
    is_editable = serializers.BooleanField(label="拼团是否可以编辑")


class AdminGrouponSerializer(GrouponBasicSerializer):
    """后台拼团活动详情序列化器类"""

    groupon_id = serializers.IntegerField(source="id", label="拼团id")
    product = GrouponProductSerializer(label="拼团商品信息")
    price = FuncField(lambda value: round(float(value), 2), label="拼团价格")
    attend_limit = serializers.IntegerField(label="参团上限")
    from_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动开始时间")
    to_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动结束时间")
    status = serializers.IntegerField(label="拼团活动状态 1:启用 2:停用 3:过期")
    quantity_limit = serializers.IntegerField(label="成团数量上限")
    success_size = serializers.IntegerField(label="成团人数")


class GrouponAttendBasicSerializer(serializers.Serializer):
    """拼团参与基本信息序列化器类"""

    groupon_attend_id = serializers.IntegerField(source="id", label="拼团参与id")
    size = serializers.IntegerField(label="拼团当前参与人数")
    success_size = serializers.IntegerField(label="成团人数")
    to_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团参与结束时间")


class AdminGrouponAttendSerializer(GrouponAttendBasicSerializer):
    """后台拼团参与序列化器类"""

    anonymous_size = serializers.IntegerField(label="匿名用户数量")
    sponsor = SponsorSerializer(label="团长信息")
    status = serializers.IntegerField(label="拼团参与状态 1:拼团中 2:已成团 3:已失败")
    failed_reason = serializers.CharField(label="失败原因")
    groupon = GrouponBasicSerializer(label="团基本信息")
    create_time = serializers.DateTimeField(source="create_at", format=DateFormat.TIME, label="开团时间")
    success_time = serializers.DateTimeField(
        source="update_at", format=DateFormat.TIME, label="成团时间(数据改变时间)"
    )

