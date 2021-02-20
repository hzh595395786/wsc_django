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