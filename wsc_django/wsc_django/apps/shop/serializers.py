import re
from rest_framework import serializers
from django.db import transaction

from config.services import create_receipt_by_shop
from delivery.services import create_delivery_config, create_pick_period_line
from product.services import create_default_group_by_shop
from shop.services import create_shop
from shop.models import Shop
from staff.services import create_super_admin_staff


class ShopCreateSerializer(serializers.ModelSerializer):
    """创建商铺序列化器类"""

    class Meta:
        model = Shop
        fields = (
            'shop_name', 'shop_img', 'shop_province','shop_city','shop_county','shop_address','description','inviter_phone'
        )

    def validate_inviter_phone(self, value):
        if not re.match(r'1[3-9]\d{9}', value):
            raise serializers.ValidationError("推荐人手机号格式不正确")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
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
                create_default_group_by_shop(shop.id)
                # 将店铺创建者创建为超级管理员员工
                create_super_admin_staff(shop, shop.super_admin)
            except Exception as e:
                # 回滚到保存点
                transaction.savepoint_rollback(save_id)
                raise
            # 提交事务
            transaction.savepoint_commit(save_id)
        return shop


