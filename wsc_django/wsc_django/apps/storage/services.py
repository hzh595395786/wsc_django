from storage.constant import PRODUCT_STORAGE_RECORD_TYPE
from storage.models import ProductStorageRecord


def create_product_storage_record(record_info: dict):
    """
    创建一条库存变更记录
    :param record_info:{
        "shop_id": 1,
        "product_id": 1,
        "operator_type": 1,
        "user_id": 1,
        "type": 1,
        "change_storage": 1,
        "current_storage": 2,
        "order_num": 1xxxxx,
    }
    :return:
    """
    record = ProductStorageRecord(**record_info)
    record.save()
    return record


def create_product_storage_records(storage_record_list: list):
    """
    创建多条库存变更记录
    :param storage_record_list: [{},{}]
    :return: storage_record_list:[库存记录对象]
    """
    record_list = [ProductStorageRecord(**storage_record) for storage_record in storage_record_list]
    storage_record_list = ProductStorageRecord.objects.bulk_create(record_list)
    return storage_record_list


def list_product_storage_record_by_product_id(
    shop_id: int, product_id: int
):
    """
    查询一个货品的库存变更记录
    :param shop_id:
    :param product_id:
    :return:
    """
    record_list = (
        ProductStorageRecord.objects.filter(shop_id=shop_id, product_id=product_id)
        .order_by('-create_time')
        .all()
    )
    for record in record_list:
        record.type_text = PRODUCT_STORAGE_RECORD_TYPE.get(record.type, "")
    return record_list