from config.constant import PrinterStatus
from config.models import Receipt, Printer
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


def get_printer_by_shop_id(shop_id: int, filter_delete: bool = True):
    """
    查找店铺的打印机
    :param shop_id:
    :param filter_delete:
    :return:
    """
    printer_query = Printer.objects.filter(shop_id=shop_id)
    if filter_delete:
        printer_query = printer_query.exclude(status=PrinterStatus.DELETE)
    printer = printer_query.first()
    return printer


def get_receipt_by_shop_id(shop_id: int):
    """
    通过shop_id查找一个商铺的小票设置
    :param shop_id:
    :return:
    """
    receipt = Receipt.objects.filter(id=shop_id).first()
    return receipt