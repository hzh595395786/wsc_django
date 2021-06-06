from rest_framework import serializers
from django.db import transaction

from delivery.services import create_delivery_config, create_pick_period_line
from product.services import create_default_group_by_shop
from shop.constant import ShopStatus
from shop.services import create_shop, create_shop_reject_reason_by_shop_id, create_pay_channel, \
    create_shop_creator_history_realname
from staff.services import create_super_admin_staff
from user.serializers import UserSerializer, operatorSerializer
from wsc_django.utils.constant import DateFormat
from config.services import (
    create_receipt_by_shop,
    create_share_setup,
    create_some_config_by_shop_id,
    create_msg_notify_by_shop_id
)
from wsc_django.utils.validators import (
    mobile_validator,
    shop_verify_status_validator,
    shop_verify_type_validator,
    shop_status_validator,
)


class ShopCreateSerializer(serializers.Serializer):
    """总后台创建商铺序列化器类"""

    id = serializers.IntegerField(read_only=True, label="商铺id")
    shop_code = serializers.CharField(read_only=True, label="商铺code")
    shop_name = serializers.CharField(required=True, max_length=128, label="商铺名称")
    shop_img = serializers.CharField(required=True, max_length=300, label="商铺logo")
    shop_province = serializers.CharField(required=True, label="商铺省份编号")
    shop_city = serializers.CharField(required=True, label="商铺城市编号")
    shop_county = serializers.CharField(required=True, label="商铺区编号")
    shop_address = serializers.CharField(required=True, max_length=100, label="详细地址")
    description = serializers.CharField(required=True, max_length=200, label="商铺描述")
    inviter_phone = serializers.CharField(required=False, validators=[mobile_validator], label="推荐人手机号")
    realname = serializers.CharField(required=False, label="历史真实姓名")

    def create(self, validated_data):
        user = self.context['user']
        # 申请时的历史真实姓名
        history_realname = validated_data.pop("realname", None)
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()
            try:
                # 创建商铺
                shop = create_shop(validated_data, user)
                # 创建小票
                create_receipt_by_shop(shop.id)
                # 创建默认配送设置
                delivery_config = create_delivery_config(shop.id)
                create_pick_period_line(delivery_config, "12:00", "13:00")
                create_pick_period_line(delivery_config, "17:00", "18:00")
                create_pick_period_line(delivery_config, "21:00", "22:00")
                # 创建默认商品分组
                create_default_group_by_shop(shop)
                # 将店铺创建者创建为超级管理员员工
                create_super_admin_staff(shop, shop.super_admin)
                # 创建店铺分享设置
                create_share_setup(shop.id, shop.shop_name)
                # 创建一些奇怪的设置
                create_some_config_by_shop_id(shop.id)
                # 创建默认消息通知配置
                create_msg_notify_by_shop_id(shop.id)
                # 储存申请者的历史真实姓名
                if history_realname:
                    create_shop_creator_history_realname(shop.id, history_realname)
            except Exception as e:
                print(e)
                # 回滚到保存点
                transaction.savepoint_rollback(save_id)
                raise
            # 提交事务
            transaction.savepoint_commit(save_id)
        return shop


class SuperShopSerializer(serializers.Serializer):
    """总后台商铺详情序列化器"""

    shop_id = serializers.IntegerField(read_only=True, source="id", label="商铺id")
    shop_name = serializers.CharField(label="商铺名称")
    shop_img = serializers.CharField(label="商铺logo")
    shop_province = serializers.CharField(label="商铺省份编号")
    shop_city = serializers.CharField(label="商铺城市编号")
    shop_county = serializers.CharField(label="商铺区编号")
    shop_address = serializers.CharField(label="详细地址")
    description = serializers.CharField(label="商铺描述")
    create_time = serializers.DateTimeField(label="商铺创建时间")
    shop_status = serializers.IntegerField(source="status", label="商铺状态")
    create_user_data = UserSerializer(read_only=True, label="商铺创建人信息")
    super_admin_data = UserSerializer(label="超管信息")


class SuperShopListSerializer(serializers.Serializer):
    """总后台商铺列表序列化器类"""

    shop_id = serializers.IntegerField(read_only=True, source="id", label="商铺id")
    shop_name = serializers.CharField(label="商铺名称")
    shop_img = serializers.CharField(label="商铺logo")
    product_species_count = serializers.IntegerField(label="商铺货品种类数量")
    is_super_admin = serializers.IntegerField(label="该用户是否为该店的超级管理员")
    shop_status = serializers.IntegerField(source="status", label="商铺状态")
    cerify_active = serializers.IntegerField(label="商铺是否认证")
    pay_active = serializers.IntegerField(label="商铺是否开通支付")
    shop_verify_content = serializers.CharField(label="商铺认证内容")


class AdminShopSerializer(serializers.Serializer):
    """后台商铺信息序列化器类"""

    shop_id = serializers.IntegerField(read_only=True, source="id", label="商铺id")
    shop_name = serializers.CharField(label="商铺名称")
    shop_img = serializers.CharField(label="商铺logo")
    shop_phone = serializers.CharField(label="商铺联系电话")
    shop_status = serializers.IntegerField(source="status", label="商铺状态")
    shop_province = serializers.CharField(label="商铺省份编号")
    shop_city = serializers.CharField(label="商铺城市编号")
    shop_county = serializers.CharField(label="商铺区编号")
    shop_address = serializers.CharField(label="详细地址")
    shop_code = serializers.CharField(label="商铺编号")
    cerify_active = serializers.IntegerField(label="商铺是否认证")
    shop_verify_type = serializers.IntegerField(label="商铺认证类型")
    pay_active = serializers.IntegerField(label="商铺是否开通支付")
    shop_verify_content = serializers.CharField(label="商铺认证内容")
    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="商铺创建时间")
    create_user = UserSerializer(read_only=True, label="商铺创建人信息")


class MallShopSerializer(serializers.Serializer):
    """商城端商铺信息序列化器类"""

    shop_name = serializers.CharField(label="商铺名称")
    shop_code = serializers.CharField(label="商铺编号")
    shop_img = serializers.CharField(label="商铺logo")
    shop_province = serializers.CharField(label="商铺省份编号")
    shop_city = serializers.CharField(label="商铺城市编号")
    shop_county = serializers.CharField(label="商铺区编号")
    shop_address = serializers.CharField(label="详细地址")
    shop_phone = serializers.CharField(label="商铺联系电话")


class SuperShopStatusSerializer(serializers.Serializer):
    """总后台商铺状态"""

    shop_id = serializers.IntegerField(read_only=True, source="id", label="商铺id")
    shop_name = serializers.CharField(read_only=True, label="商铺名称")
    shop_img = serializers.CharField(read_only=True, label="商铺logo")
    shop_address = serializers.CharField(read_only=True, label="详细地址")
    shop_province = serializers.CharField(read_only=True, label="商铺省份编号")
    shop_city = serializers.CharField(read_only=True, label="商铺城市编号")
    shop_county = serializers.CharField(read_only=True, label="商铺区编号")
    shop_status = serializers.IntegerField(
        required=True, source="status", validators=[shop_status_validator], label="商铺状态"
    )
    create_time = serializers.DateTimeField(read_only=True, format=DateFormat.TIME, label="商铺创建时间")
    creator = UserSerializer(read_only=True, label="商铺创建者")
    operate_time = serializers.DateTimeField(read_only=True, source="update_at", format=DateFormat.TIME, label="操作时间")
    operator = operatorSerializer(read_only=True, label="审核操作人")
    reject_reason = serializers.CharField(required=False, default='', label="拒绝理由")
    description = serializers.CharField(read_only=True, label="商铺描述")
    inviter_phone = serializers.CharField(read_only=True, label="推荐人手机号")
    current_realname = serializers.CharField(read_only=True, label="创建时的用户真实姓名")

    def update(self, instance, validated_data):
        shop_status = validated_data["status"]
        instance.status = shop_status
        if shop_status == ShopStatus.REJECTED:
            create_shop_reject_reason_by_shop_id(instance.id, validated_data['reject_reason'])
        instance.save()
        return instance


class SuperShopVerifySerializer(serializers.Serializer):
    """总后台商铺认证状态"""

    shop_id = serializers.IntegerField(source='id', read_only=True, label="商铺id")
    verify_status = serializers.IntegerField(
        write_only=True, required=True, validators=[shop_verify_status_validator], label="商铺认证状态"
    )
    verify_type = serializers.IntegerField(
        write_only=True, required=True, validators=[shop_verify_type_validator], label="商铺认证类型,个人/企业"
    )
    verify_content = serializers.CharField(
        write_only=True, min_length=0, max_length=200, required=True, label="认证内容"
    )

    def update(self, instance, validated_data):
        cerify_active = validated_data["verify_status"]
        verify_type = validated_data["verify_type"]
        verify_content = validated_data["verify_content"]
        instance.cerify_active = cerify_active
        instance.shop_verify_type = verify_type
        instance.shop_verify_content = verify_content
        instance.save()
        return instance


class ShopPayChannelSerializer(serializers.Serializer):
    """总后台支付渠道序列化器类"""

    smerchant_no = serializers.CharField(label="商户号")
    terminal_id1 = serializers.CharField(label="终端号1")
    access_token = serializers.CharField(label="扫呗access_token")
    channel_type = serializers.IntegerField(label="支付渠道, 1:利楚, 2:建行")

    def create(self, validated_data):
        shop = self.context["shop"]
        shop_pay_channel = create_pay_channel(validated_data, shop.id)
        return shop_pay_channel


