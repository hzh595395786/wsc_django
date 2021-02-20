from django.db import transaction
from pypinyin import slug
from rest_framework import serializers

from wsc_django.utils.setup import ConvertDecimalPlacesField
from product.services import (
    create_product,
    create_product_picture,
    update_product_storage,
)
from storage.constant import (
    ProductStorageRecordType,
    ProductStorageRecordOperatorType,
)


class ProductCreateSerializer(serializers.Serializer):
    """创建货品序列化器类"""

    name = serializers.CharField(max_length=15, min_length=1, required=True, label="货品名称")
    group_id = serializers.IntegerField(required=True, label="货品分组id")
    price = serializers.DecimalField(max_digits=13, decimal_places=4, required=True, min_value=0, label="货品单价")
    storage = serializers.DecimalField(max_digits=13, decimal_places=4, required=True, min_value=0, label="货品库存")
    code = serializers.CharField(required=False, label="货品编码")
    summary = serializers.CharField(max_length=20, min_length=0, required=False, label="货品简介")
    pictures = serializers.ListField(
        child=serializers.CharField(max_length=15, min_length=0, required=False),
        required=False,
        label="货品轮播图",
    )
    description = serializers.CharField(required=False, label="图文描述")
    cover_image_url = serializers.CharField(required=True, label="首页图片")
    shop_id = serializers.IntegerField(read_only=True, label="商铺id")
    user_id = serializers.IntegerField(read_only=True, label="创建货品的用户id")

    def create(self, validated_data):
        user = self.context["request"].user
        shop = self.context["request"].shop
        storage = validated_data.pop("storage")
        product_pictures = validated_data.pop("pictures", None)
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()
            try:
                # 添加货品
                validated_data["shop"] = shop
                validated_data["name_acronym"] = slug(validated_data["name"], separator="")
                product = create_product(validated_data, user.id)
                if product_pictures:
                    # 添加货品轮播图
                    for pp in product_pictures:
                        create_product_picture(product.id, pp)
                # 更改库存,同时生成库存更改记录
                update_product_storage(
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


class ProductDetailSerializer(serializers.Serializer):
    """货品详情序列化器类"""

    product_id = serializers.IntegerField(source="id", label="货品名")
    group_id = serializers.IntegerField(label="货品分组id")
    group_name = serializers.CharField(label="货品分组名称")
    price = ConvertDecimalPlacesField(max_digits=13, decimal_places=4, label="货品价格")
    storage = ConvertDecimalPlacesField(max_digits=13, decimal_places=4, label="货品库存")
    pictures = serializers.ListField(allow_null=True, child=serializers.CharField(), label="货品轮播图")
    code = serializers.CharField(label="货品编码")
    summary = serializers.CharField(label="货品简介")
    cover_image_url = serializers.CharField(label="货品封面图")
    description = serializers.CharField(label="货品描述")
    status = serializers.IntegerField(label="货品状态")

    def price_convert_decimal_places(self, price):
        price = round(float(price), 2)
        return price

    def storage_convert_decimal_places(self, storage):
        storage = round(float(storage), 2)
        return storage

