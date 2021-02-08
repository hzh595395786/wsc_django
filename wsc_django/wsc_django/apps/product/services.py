from shop.models import Shop
from product.models import ProductGroup
from product.constant import (
    ProductGroupDefault
)


def create_default_group_by_shop(shop: Shop):
    """
    给商店创建一个默认分组
    :param shop: 商铺对象
    :return:
    """
    default_product_group = ProductGroup.objects.create(
        shop=shop, name="默认分组", default=ProductGroupDefault.YES
    )
    default_product_group.save()
    return default_product_group
