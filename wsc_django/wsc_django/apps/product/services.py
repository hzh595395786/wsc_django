from shop.models import Shop
from product.models import ProductGroup, Product, ProductPicture
from product.constant import (
    ProductGroupDefault,
    ProductStatus,
)
from storage.services import create_product_storage_record


def create_product(product_info: dict, user_id: int):
    """
    添加一个货品
    :param product_info:{"name": "apple", "group_id": 1, "price": 12.3, "code": "apple123",
                          "summary": "这是一个苹果", "pictures": ["http://abc", "http://bcd"],
                          "description": "这是货品描述", "cover_image_url": "http://qwe",
                          "shop_id": 104}
    :param user_id: 操作人的user_id
    :return:
    """
    product = Product.objects.create(**product_info)
    product.save()
    return product


def create_product_picture(product_id: int, image_url: str):
    """
    添加货品的一个轮播图
    :param product_id:
    :param image_url:
    :return:
    """
    product_picture = ProductPicture(product_id=product_id, image_url=image_url)
    product_picture.save()


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


def update_product_storage(
    product: Product,
    user_id: int,
    change_storage: int,
    record_type: int,
    operator_type: int,
    order_num=None,
):
    """
    更新一个商品的库存,同时生成库存更改记录
    :param product: 货品对象
    :param user_id: 操作人的user_id
    :param change_storage: 库存变更量
    :param record_type: 变更类型 手动修改1,商城售出2,订单取消3,订单退款4
    :param operator_type: 操作人类型,员工or客户
    :param order_num:
    :return:
    """
    product.storage += change_storage
    # 库存为0 自动下架
    if product.storage <= 0:
        product.status = ProductStatus.OFF
    # 生成库存变更记录
    product.save()
    product_storage_record = {
        "shop_id": product.shop.id,
        "product_id": product.id,
        "operator_type": operator_type,
        "user_id": user_id,
        "type": record_type,
        "change_storage": change_storage,
        "current_storage": product.storage,
    }
    if order_num:
        product_storage_record["order_num"] = order_num
    storage_record = create_product_storage_record(product_storage_record)
    return storage_record


def get_product_group_by_id(shop_id: int, group_id: int):
    """
    通过店铺ID与分组ID来查询货品分组
    :param shop_id:
    :param group_id:
    :return:
    """
    product_group = ProductGroup.objects.filter(shop_id=shop_id, id=group_id).first()
    return product_group


def get_product_by_id(
    shop_id: int,
    product_id: int,
    with_picture: bool = False,
    filter_delete: bool = True,
):
    """
    根据货品ID, 货品ID来获取单个货品详情, 包括轮播图
    :param shop_id:
    :param product_id:
    :param with_picture: 包括轮播图
    :param filter_delete: 过滤删除
    :return:
    """
    # 查询货品信息, 包括分组名
    product_query = Product.objects.filter(id=product_id, shop_id=shop_id)
    if product_query and filter_delete:
        product_query = product_query.exclude(status=ProductStatus.DELETED)
    product = product_query.first()
    # 查询货品轮播图
    if product and with_picture:
        product_pictures = ProductPicture.objects.filter(product_id=product_id).all()
        product.pictures = [pp.image_url for pp in product_pictures]
    return product


def get_product_with_group_name(shop_id: int, product_id: int):
    """
    获取一个货品信息,并附带分组名
    :param shop_id:
    :param product_id:
    :return:
    """
    product = get_product_by_id(shop_id, product_id)
    if product:
        product_group = get_product_group_by_id(shop_id, product.group_id)
        product.group_name = product_group.name
        product.group_id = product_group.id
    return product