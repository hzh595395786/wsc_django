from product.services import list_product_ids_by_shop_id


def list_product_ids_by_shop_id_interface(shop_id: int, status: list):
    """列出一个店铺的商品ID列表interface"""
    product_ids = list_product_ids_by_shop_id(shop_id, status)
    return product_ids