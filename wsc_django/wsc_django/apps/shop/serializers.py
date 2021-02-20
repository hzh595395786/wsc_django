from rest_framework import serializers
from django.db import transaction

from config.services import create_receipt_by_shop
from delivery.services import create_delivery_config, create_pick_period_line
from product.services import create_default_group_by_shop
from shop.services import create_shop
from staff.services import create_super_admin_staff
from staff.serializers import StaffDetailSerializer
from wsc_django.utils.validators import mobile_validator


class ShopCreateSerializer(serializers.Serializer):
    """创建商铺序列化器类"""

    id = serializers.IntegerField(read_only=True, label="商铺id")
    shop_code = serializers.CharField(read_only=True, label="商铺code")
    shop_name = serializers.CharField(required=True, max_length=128, label="商铺名称")
    shop_img = serializers.CharField(required=True, max_length=300, label="商铺logo")
    shop_province = serializers.CharField(required=True, label="商铺省份编号")
    shop_city = serializers.CharField(required=True, label="商铺城市编号")
    shop_county = serializers.CharField(required=True, label="商铺区编号")
    shop_address = serializers.CharField(required=True, max_length=100, label="详细地址")
    description = serializers.CharField(required=True, max_length=200, label="商铺描述")
    inviter_phone = serializers.CharField(required=True, validators=[mobile_validator], label="推荐人手机号")

    def create(self, validated_data):
        user = self.context['user']
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()
            try:
                # 创建商铺
                shop = create_shop(validated_data, user)
                # 创建小票
                create_receipt_by_shop(shop)
                # 创建默认配送设置
                delivery_config = create_delivery_config(shop)
                create_pick_period_line(delivery_config, "12:00", "13:00")
                create_pick_period_line(delivery_config, "17:00", "18:00")
                create_pick_period_line(delivery_config, "21:00", "22:00")
                # 创建默认商品分组
                create_default_group_by_shop(shop)
                # 将店铺创建者创建为超级管理员员工
                create_super_admin_staff(shop, shop.super_admin)
            except Exception as e:
                print(e)
                # 回滚到保存点
                transaction.savepoint_rollback(save_id)
                raise
            # 提交事务
            transaction.savepoint_commit(save_id)
        return shop


class ShopDetailSerializer(serializers.Serializer):
    """商铺详情序列化器"""

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
    create_user = StaffDetailSerializer(read_only=True, label="商铺创建人信息")


class ShopListSerializer(serializers.Serializer):
    """商铺列表序列化器类"""

    shop_id = serializers.IntegerField(read_only=True, source="id", label="商铺id")
    shop_name = serializers.CharField(label="商铺名称")
    shop_img = serializers.CharField(label="商铺logo")
    # product_count = serializers.IntegerField(label="店铺商品数量")
    is_super_admin = serializers.IntegerField(label="该用户是否为该店的超级管理员")
    shop_status = serializers.IntegerField(source="status", label="商铺状态")
    cerify_active = serializers.IntegerField(label="店铺是否认证")
    pay_active = serializers.IntegerField(label="店铺是否开通支付")
    shop_verify_content = serializers.CharField(label="认证内容")