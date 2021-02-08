from config.models import Receipt
from shop.models import Shop


def create_receipt_by_shop(shop: Shop):
    """
    为店铺创建一个默认小票
    :param shop: 商铺对象
    :return:
    """
    receipt = Receipt.objects.create(id=shop)
    receipt.save()
    return receipt