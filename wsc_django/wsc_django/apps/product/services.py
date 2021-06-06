from collections import defaultdict

from django.db.models import Count, Q

from logs.constant import ProductLogType
from logs.services import create_product_log
from promotion.constant import PromotionType
from promotion.services import get_product_promotion, set_product_promotion, list_product_promotions
from shop.models import Shop
from product.models import ProductGroup, Product, ProductPicture
from product.constant import (
    ProductGroupDefault,
    ProductOperationType,
    ProductStatus,
)
from storage.services import create_product_storage_record


#################  货品相关  ##################
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
    product = Product(**product_info)
    product.save()
    # 生成操作记录
    log_info = {
        "shop_id": product.shop.id,
        "operator_id": user_id,
        "operate_type": ProductLogType.ADD_PRODUCT,
        "operate_content": product.name,
    }
    create_product_log(log_info)
    return product


def create_product_pictures(product_id: int, image_url_list: list):
    """
    添加货品的一个轮播图
    :param product_id:
    :param image_url:
    :return:
    """
    product_picture_list = []
    for image_url in image_url_list:
        product_picture = ProductPicture(product_id=product_id, image_url=image_url)
        product_picture_list.append(product_picture)
    product_pictures = ProductPicture.objects.bulk_create(product_picture_list)
    return product_pictures


def update_product_storage_and_create_record(
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


def update_product_storage_and_no_record(
    product: Product,
    user_id: int,
    change_storage: int,
    record_type: int,
    operator_type: int,
    order_num=None,
):
    """
    更新一个商品的库存,但不生成库存更改记录
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
    return product_storage_record


def update_product_product_group_by_ids(product_ids: list, group_id):
    """
    更新货品的分组
    :param product_ids:
    :param group_id:
    :return:
    """
    Product.objects.filter(id__in=product_ids).update(group_id=group_id)


def update_products_status(
    product_list: list, operation_type: int, product_ids_set: set
):
    """
    批量修改货品的状态（上架，下架)
    :param product_list:
    :param operation_type: 1:上架，2：下架
    :return:
    """
    product_name_list = []
    if operation_type == ProductOperationType.ON:
        status = ProductStatus.ON
    else:
        status = ProductStatus.OFF
    for p in product_list:
        # 跳过库存不足的货品
        if (
            status == ProductOperationType.ON
            and p.storage <= 0
        ):
            continue
        # 跳过可能存在拼团活动的货品
        if (
            status == ProductOperationType.OFF
            and p.id in product_ids_set
        ):
            continue
        p.status = status
        p.save()
        product_name_list.append(p.name)
    return product_name_list


def delete_product_picture_by_product_id(product_id: int):
    """
    通过货品ID删除对应的轮播图
    :param product_id:
    :return:
    """
    ProductPicture.objects.filter(product_id=product_id).delete()


def delete_product_by_ids_and_shop_id(
        product_list: list, product_ids_set: set
):
    """
    根据货品id列表和商铺id删除货品
    :param product_list
    :param product_ids_set:
    :return:
    """
    product_name_list = []
    for product in product_list:
        # 跳过可能存在拼团活动的货品
        if product.id in product_ids_set:
            continue
        product.status = ProductStatus.DELETED
        product.save()
        product_name_list.append(product.name)
    return product_name_list


def sort_shop_product_group(shop_id: int, group_ids: list):
    """
    给一个店铺的货品分组排序
    :param shop_id:
    :param group_ids:
    :return:
    """
    # 按照传过来的group_id的顺序排序
    product_group_list = list_product_group_by_shop_id(shop_id)
    group_id_2_group = {pgl.id: pgl for pgl in product_group_list}
    for i, id in enumerate(group_ids):
        group = group_id_2_group.get(id)
        # 防止存在已删除的分组
        if group:
            group.sort = i
            group.save()


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
    if product and not with_picture:
        product.pictures = []
    return product


def get_product_with_group_name(shop_id: int, product_id: int):
    """
    获取一个货品信息,并附带分组名
    :param shop_id:
    :param product_id:
    :return:
    """
    product = get_product_by_id(shop_id, product_id, with_picture=True)
    if product:
        # 营销信息
        promotion = get_product_promotion(shop_id, product.id)
        set_product_promotion(product, promotion)
        product_group = get_product_group_by_shop_id_and_id(shop_id, product.group_id)
        product.group_name = product_group.name
        product.group_id = product_group.id
    return product


def list_product_by_ids(shop_id: int, product_ids: list, filter_delete: bool = True):
    """
    通过商铺id和货品id列表获取货品列表
    :param shop_id:
    :param product_ids:
    :param filter_delete: 过滤删除
    :return:
    """
    product_list_query = Product.objects.filter(shop_id=shop_id, id__in=product_ids)
    if filter_delete:
        product_list_query = product_list_query.exclude(status=ProductStatus.DELETED)
    product_list = product_list_query.all()
    return product_list


def list_product_by_group_id_and_shop_id(
    shop_id: int, group_id: int, filter_delete: bool = True
):
    """

    :param shop_id:
    :param group_id:
    :param filter_delete: 过滤删除
    :return:
    """
    product_list_query = Product.objects.filter(group_id=group_id, shop_id=shop_id)
    if filter_delete:
        product_list_query = product_list_query.exclude(status=ProductStatus.DELETED)
    product_list = product_list_query.all()
    return product_list


def list_product_by_filter(
    shop_id: int,
    status: list,
    keyword: str,
    group_id: int,
    promotion_types: list = None
):
    """
    根据店铺ID, 关键字, 分组ID, 货品状态获取货品列表
    :param shop_id:
    :param group_id:
    :param keyword:
    :param status:
    :param promotion_types:
    :return:
    """
    product_list_query = Product.objects.filter(shop_id=shop_id, status__in=status)
    if keyword:
        product_list_query = product_list_query.filter(
            Q(name__contains=keyword) |
            Q(name_acronym__contains=keyword)
        )
    if group_id > 0:
        product_list_query = product_list_query.filter(group_id=group_id)
    # 营销玩法筛选, 转换成基于id的筛选
    map_product_promotions = list_product_promotions(shop_id)
    if promotion_types:
        # 活动商品归类
        map_promotion_products = defaultdict(set)
        for product_id, promotion in map_product_promotions.items():
            map_promotion_products[int(promotion._event_type)].add(
                product_id
            )  # promotion._event_type str
        all_product_id = list_product_ids_by_shop_id(shop_id, status)
        normal_product_ids = set(all_product_id) - set(map_product_promotions.keys())
        map_promotion_products[PromotionType.NORMAL] = normal_product_ids
        groupon_product_ids = set()
        for promotion_type in promotion_types:
            groupon_product_ids.update(
                map_promotion_products.get(promotion_type, set())
            )
        product_list_query = product_list_query.filter(id__in=groupon_product_ids)
    product_list_query = product_list_query.order_by('status', '-id')
    product_list = product_list_query.all()
    # 拼装营销活动类型
    for product in product_list:
        promotion = map_product_promotions.get(product.id)
        promotion_type = (
            int(promotion._event_type) if promotion else PromotionType.NORMAL
        )
        assert promotion_type in [PromotionType.NORMAL, PromotionType.GROUPON]
        product.promotion_type = promotion_type
    return product_list


def list_product_by_shop_id(shop_id: int, status=None):
    """
    通过商店ID查询旗下的所有的所有货品
    :param shop_id:
    :param status:
    :return:
    """
    product_query = Product.objects.filter(shop_id=shop_id)
    if isinstance(status, int):
        product_query = product_query.filter(status=status)
    elif isinstance(status, list):
        product_query = product_query.filter(status__in=status)
    product_list = product_query.all()
    # 获取商品营销玩法信息
    map_product_promotions = list_product_promotions(shop_id)
    for product in product_list:
        promotion = map_product_promotions.get(product.id)
        set_product_promotion(product, promotion)
    return product_list


def list_product_ids_by_shop_id(shop_id: int, status: list):
    """
    通过商店ID查询旗下的所有的所有货品ID
    :param shop_id:
    :param status:
    :return:
    """
    product_ids = Product.objects.filter(shop_id=shop_id, status__in=status).values("id")
    # 得到的是一个queryset,queryset无法set化
    product_id_list = [product_id_dict["id"] for product_id_dict in product_ids]
    return product_id_list


#####################  货品分组相关  #####################
def create_product_group(shop_id: int, user_id: int, product_group_info: dict):
    """
    创建一个货品分组
    :param shop_id:
    :param user_id:
    :param product_group_info:{"name": "分组1", "description":"描述"}
    :return:
    """
    product_group = ProductGroup.objects.create(shop_id=shop_id, **product_group_info)
    product_group.set_default_sort()
    product_group.save()
    # 记录日志
    log_info = {
        "shop_id": product_group.shop_id,
        "operator_id": user_id,
        "operate_type": ProductLogType.ADD_PRODUCT_GROUP,
        "operate_content": product_group.name,
    }
    create_product_log(log_info)
    return product_group


def create_default_group_by_shop(shop: Shop):
    """
    给商店创建一个默认分组
    :param shop: 商铺对象
    :return:
    """
    default_product_group = ProductGroup.objects.create(
        shop=shop, name="默认分组", default=ProductGroupDefault.YES
    )
    default_product_group.set_default_sort()
    default_product_group.save()
    return default_product_group


def update_product_group(
    product_group: ProductGroup,
    user_id: int,
    shop_id: int,
    name: str,
    description: str,
):
    """
    编辑分组信息
    :param product_group:
    :param user_id:
    :param shop_id:
    :param name:
    :param description:
    :return:
    """
    product_group.name = name
    product_group.description = description
    product_group.save()
    change = bool(product_group.name == name)
    if change:
        # 记录日志
        log_info = {
            "shop_id": shop_id,
            "operator_id": user_id,
            "operate_type": ProductLogType.UPDATE_PRODUCT_GROUP,
            "operate_content": name,
        }
        create_product_log(log_info)
    return product_group


def delete_product_group_by_id_and_shop_id(
    product_group: ProductGroup, group_id: int, shop_id: int, user_id: int
):
    """
    删除一个货品分组
    :param product_group:
    :param group_id:
    :param shop_id:
    :param user_id:
    :return:
    """
    if product_group.default == ProductGroupDefault.YES:
        return False, "默认分组不可删除"
    # 获取分组下货品
    product_list = list_product_by_group_id_and_shop_id(
        shop_id, group_id, filter_delete=False
    )
    # 获取默认分组
    default_product_group = get_default_product_by_shop_id(shop_id)
    # 修改货品所属分组为默认分组
    product_list.update(group_id=default_product_group.id)
    product_group.delete()
    # 记录日志
    log_info = {
        "shop_id": shop_id,
        "operator_id": user_id,
        "operate_type": ProductLogType.DELETE_PRODUCT_GROUP,
        "operate_content": product_group.name,
    }
    create_product_log(log_info)
    return True, ""


def get_product_group_by_shop_id_and_id(shop_id: int, group_id: int):
    """
    通过店铺ID与分组ID来查询货品分组
    :param shop_id:
    :param group_id:
    :return:
    """
    product_group = ProductGroup.objects.filter(shop_id=shop_id, id=group_id).first()
    return product_group


def get_default_product_by_shop_id(shop_id: int):
    """
    查询一个货品的默认分组
    :param shop_id:
    :return:
    """
    product_group = ProductGroup.objects.filter(shop_id=shop_id, default=ProductGroupDefault.YES).first()
    return product_group


def count_product_by_shop_ids(shop_ids: list):
    """
    通过店铺id列表查找商铺的货品种类数量
    :param shop_ids: 商铺id列表
    :return:
    """
    shop_product_count_dict = {shop_id: 0 for shop_id in shop_ids}
    product_list = (
        Product.objects.filter(shop_id__in=shop_ids)
        .exclude(status=ProductStatus.DELETED)
        .all()
    )
    for product in product_list:
        shop_product_count_dict[product.shop.id] += 1
    return shop_product_count_dict


def list_product_group_by_shop_id(shop_id: int):
    """
    通过商铺id查询旗下的所有分组信息
    :param shop_id:
    :return:
    """
    product_group_list = ProductGroup.objects.filter(shop_id=shop_id).order_by('sort').all()
    return product_group_list


def list_product_group_with_product_count(shop_id: int, status: list):
    """
    查询所有的分组并且包含分组对应的货品数量
    :param shop_id:
    :param status:
    :return:
    """
    # 查询分组信息
    product_group_list = list_product_group_by_shop_id(shop_id)
    # 查询货品数量
    product_count_list = (
        ProductGroup.objects.filter(shop_id=shop_id, product__status__in=status).
        order_by('sort').
        annotate(count=Count("product")).
        all()
    )
    product_count_dict = {product_group.id: product_group.count for product_group in product_count_list}
    for pg in product_group_list:
        pg.product_count = product_count_dict.get(pg.id, 0)
    return product_group_list


def list_product_group_with_product_list(
        shop_id: int, status: int = ProductStatus.ON
):
    """
    通过商店ID查询所有分组,并且将分组下的货品信息挂载
    :param shop_id:
    :param status:
    :return:
    """
    # 查询分组信息
    product_group_list = list_product_group_by_shop_id(shop_id)
    product_list = list_product_by_shop_id(shop_id, status)
    product_group_index_dict = {}
    for index, pgl in enumerate(product_group_list):
        product_group_index_dict[pgl.id] = index
        pgl.products = []
    for pl in product_list:
        product_group_list[product_group_index_dict[pl.group_id]].products.append(pl)
    return product_group_list