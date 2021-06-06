from django.db import transaction
from pypinyin import slug
from rest_framework import serializers

from user.serializers import UserSerializer
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.core import FuncField
from product.services import (
    create_product,
    create_product_group,
    create_product_pictures,
    update_product_storage_and_create_record,
    delete_product_picture_by_product_id,
    update_product_group
)
from storage.constant import (
    ProductStorageRecordType,
    ProductStorageRecordOperatorType,
)


class ProductGrouponSerializer(serializers.Serializer):
    """货品拼团活动序列化器类"""

    groupon_id = serializers.IntegerField(source="id", label="拼团id")
    price = FuncField(lambda value: round(float(value), 2), label="拼团价格")
    to_datetime = serializers.DateTimeField(format=DateFormat.TIME, label="拼团活动结束时间")
    groupon_type = serializers.IntegerField(label="拼团活动类型 1:普通 2:老带新")
    success_size = serializers.IntegerField(label="成团人数")
    quantity_limit = serializers.IntegerField(label="成团数量上限")
    succeeded_quantity = FuncField(lambda value: round(float(value), 2), label="已成团件数")


class ProductCreateSerializer(serializers.Serializer):
    """创建货品序列化器类"""

    product_id = serializers.IntegerField(source="id", read_only=True, label="货品id")
    name = serializers.CharField(max_length=15, min_length=1, required=True, label="货品名称")
    group_id = serializers.IntegerField(required=True, label="货品分组id")
    price = serializers.DecimalField(
        max_digits=13, decimal_places=4, required=True, min_value=0, label="货品单价"
    )
    storage = serializers.DecimalField(
        max_digits=13, decimal_places=4, required=True, min_value=0, label="货品库存"
    )
    code = serializers.CharField(allow_blank=True, required=False, label="货品编码")
    summary = serializers.CharField(
        allow_blank=True, max_length=20, min_length=0, required=False, label="货品简介"
    )
    pictures = serializers.ListField(
        child=serializers.CharField(required=False),
        allow_empty=True,
        required=False,
        label="货品轮播图",
    )
    description = serializers.CharField(required=False, allow_blank=True, label="图文描述")
    cover_image_url = serializers.CharField(required=True, label="首页图片")
    shop_id = serializers.IntegerField(required=True, label="商铺id")
    user_id = serializers.IntegerField(read_only=True, label="创建货品的用户id")

    def create(self, validated_data):
        user = self.context["self"].current_user
        storage = validated_data.pop("storage")
        product_pictures = validated_data.pop("pictures")
        validated_data["name_acronym"] = slug(validated_data["name"], separator="")
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()
            try:
                # 添加货品
                product = create_product(validated_data, user.id)
                # 添加货品轮播图
                create_product_pictures(product.id, product_pictures)
                # 更改库存,同时生成库存更改记录
                update_product_storage_and_create_record(
                    product,
                    user.id,
                    storage,
                    ProductStorageRecordType.MANUAL_MODIFY,
                    ProductStorageRecordOperatorType.STAFF,
                )
            except Exception as e:
                print(e)
                # 回滚到保存点
                transaction.savepoint_rollback(save_id)
                raise
            # 提交事务
            transaction.savepoint_commit(save_id)
        return product


class AdminProductsSerializer(serializers.Serializer):
    """后台货品列表序列化器类"""

    product_id = serializers.IntegerField(read_only=True, source="id", label="货品名")
    name = serializers.CharField(required=True, label="货品名")
    price = FuncField(lambda value: round(float(value), 2), label="货品价格")
    storage = FuncField(lambda value: round(float(value), 2), label="货品库存")
    status = serializers.IntegerField(read_only=True, label="货品状态")
    cover_image_url = serializers.CharField(required=False, label="货品封面图")
    promotion_type = serializers.IntegerField(required=False, label="商品活动信息 1: 普通 5: 拼团")


class AdminProductSerializer(AdminProductsSerializer):
    """后台货品序列化器类"""

    group_id = serializers.IntegerField(required=False, label="货品分组id")
    group_name = serializers.CharField(read_only=True, label="货品分组名称")
    pictures = serializers.ListField(
        required=False, allow_empty=True, child=serializers.CharField(), label="货品轮播图"
    )
    code = serializers.CharField(required=False, allow_blank=True, label="货品编码")
    summary = serializers.CharField(required=False, allow_blank=True, label="货品简介")
    description = serializers.CharField(required=False, allow_blank=True, label="货品描述")
    groupon = ProductGrouponSerializer(required=False, label="商品拼团信息")

    def update(self, instance, validated_data):
        shop = self.context["self"].current_shop
        user = self.context["self"].current_user
        validated_data["shop_id"] = shop.id
        product_pictures = validated_data.pop("pictures", None)
        new_storage = validated_data.pop("storage")
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()
            try:
                # 更新货品信息
                for k, v in validated_data.items():
                    setattr(instance, k, v)
                instance.save()
                if product_pictures:
                    # 更新货品轮播图信息,先删除,再添加
                    delete_product_picture_by_product_id(instance.id)
                    create_product_pictures(instance.id, product_pictures)
                    # 更改库存,同时生成库存更改记录
                change_storage = new_storage - instance.storage
                if change_storage != 0:
                    update_product_storage_and_create_record(
                        instance,
                        user.id,
                        change_storage,
                        ProductStorageRecordType.MANUAL_MODIFY,
                        ProductStorageRecordOperatorType.STAFF,
                    )
            except Exception as e:
                print(e)
                # 回滚到保存点
                transaction.savepoint_rollback(save_id)
                raise
            # 提交事务
            transaction.savepoint_commit(save_id)
        return instance


class AdminProductGroupSerializer(serializers.Serializer):
    """后台货品分组序列化器类"""

    group_id = serializers.IntegerField(read_only=True, required=False, source="id", label="分组id")
    name = serializers.CharField(required=True, min_length=1, max_length=10, label="分组名称")
    description = serializers.CharField(required=False, allow_blank=True, min_length=0, max_length=50, label="分组描述")
    default = serializers.IntegerField(required=False, label="默认分组")
    product_count = serializers.IntegerField(read_only=True, label="分组下的货品数量")
    products = AdminProductSerializer(read_only=True, many=True, label="分组商品列表")

    def create(self, validated_data):
        shop = self.context["self"].current_shop
        user = self.context["self"].current_user
        product_group = create_product_group(shop.id, user.id, validated_data)
        return product_group

    def update(self, instance, validated_data):
        # 更新一个货品分组的信息
        user = self.context["self"].current_user
        shop = self.context["self"].current_shop
        instance = update_product_group(instance, user.id, shop.id, **validated_data)
        return instance


class AdminProductSaleRecordSerializer(serializers.Serializer):
    """后台货品销售记录序列化器类"""

    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="创建时间")
    order_num = serializers.CharField(label="订单号")
    price_net = FuncField(lambda value: round(float(value), 2), label="单价（优惠后）")
    quantity_net = FuncField(lambda value: round(float(value), 2), label="量（优惠后）")
    amount_net = FuncField(lambda value: round(float(value), 2), label="金额（优惠后）")
    customer = UserSerializer(label="客户信息")


class MallProductSerializer(AdminProductSerializer):
    """商城端货品序列化器类"""
    pass # 继承父类


class MallProductGroupSerializer(AdminProductGroupSerializer):
    """商城端货品分组序列化器类"""
    pass # 继承父类


