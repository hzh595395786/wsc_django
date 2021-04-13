import datetime

from pvuv.models import ProductBrowseRecord


def create_product_browse_record(info: dict):
    """
    创建一条货品浏览记录
    :param info: {
        "shop_id": int,
        "user_id": int,
        "product_id": int,
        "start_time": datetime,
        "duration": int,
        "pre_page_name": str,
        "next_page_name": str
    }
    :return:
    """
    record = ProductBrowseRecord.objects.filter(**info)
    record.save()


def list_product_browse_record_by_id(
    shop_id: int,
    product_id: int,
    from_date: datetime,
    to_date: datetime,
):
    """
    获取一个商品的访问记录列表
    :param shop_id:
    :param product_id:
    :param from_date:
    :param to_date:
    :return:
    """
    record_list = (
        ProductBrowseRecord.objects.filter(
            shop_id=shop_id, product_id=product_id, start_time__range=[from_date, to_date]
        )
        .order_by("-start_time", "id")
        .all()
    )
    return record_list