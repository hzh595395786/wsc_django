from config.constant import PrinterStatus, ShareSetUpTemplate
from config.models import Receipt, Printer, ShareSetup, SomeConfig, MsgNotify
from shop.models import Shop


def create_receipt_by_shop(shop_id: int):
    """
    为店铺创建一个默认小票
    :param shop_id: 商铺id
    :return:
    """
    receipt = Receipt(id=shop_id)
    receipt.save()
    return receipt


def create_share_setup(shop_id: int, shop_name: str):
    """
    创建一个店铺的share_setup
    :param shop_id:
    :param shop_name:
    :return:
    """
    custom_title_name = ShareSetUpTemplate.CUSTOM_TITLE_NAME.format(shop_name=shop_name)
    custom_share_description = ShareSetUpTemplate.CUSTOM_SHARE_DESCRIPTION
    share_setup = ShareSetup(
        id=shop_id,
        custom_title_name=custom_title_name,
        custom_share_description=custom_share_description,
    )
    share_setup.save()
    return share_setup


def create_some_config_by_shop_id(shop_id: int):
    """
    为店铺创建一些奇奇怪怪的设置
    :param shop_id:
    :return:
    """
    config_info = {"id": shop_id}
    some_config = SomeConfig(**config_info)
    some_config.save()
    return some_config


def create_printer_by_shop_id(shop_id: int, printer_info: dict):
    """
    通过店铺ID给店铺添加一个打印机,目前一个店铺仅支持一个打印机
    :param shop_id:
    :param printer_info: {
        "brand": 1,
        "code": "xxxxxxxxx",
        "key": "xxxxxxxxx",
        "auto_print": 1,
    }
    :return:
    """
    printer = get_printer_by_shop_id(shop_id)
    if not printer:
        printer_info["shop_id"] = shop_id
        printer = Printer(**printer_info)
        printer.save()
    else:
        for k, v in printer_info.items():
            setattr(printer, k, v)
    return printer


def create_receipt_by_shop_id(shop_id: int):
    """
    通过shop_id为店铺创建一个默认小票
    :param shop_id:
    :return:
    """
    receipt = Receipt(id=shop_id)
    receipt.save()
    return receipt


def create_msg_notify_by_shop_id(shop_id: int):
    """
    通过店铺ID创建一个店铺的消息通知
    :param shop_id:
    :return:
    """
    msg_notify = MsgNotify(id=shop_id)
    msg_notify.save()
    return msg_notify


def update_share_setup(shop_id: int, args: dict):
    """
    编辑店铺分享配置
    :param shop_id:
    :param args:
    :return:
    """
    shop_share = get_share_setup_by_id(shop_id)
    for k, v in args.items():
        setattr(shop_share, k, v)
    shop_share.save()
    return shop_share


def update_some_config_by_shop_id(shop_id: int, new_config: dict):
    """
    更改一些奇怪的配置
    :param shop_id:
    :param new_config:
    :return:
    """
    some_config = get_some_config_by_shop_id(shop_id)
    for k, v in new_config.items():
        setattr(some_config, k, v)
    some_config.save()
    return some_config


def update_receipt_by_shop_id(shop_id: int, receipt_info):
    """
    通过shop_id更新其对应的小票设置
    :param shop_id:
    :param receipt_info:
    :return:
    """
    receipt = get_receipt_by_shop_id(shop_id)
    if not receipt:
        receipt = create_receipt_by_shop_id(shop_id)
    for k, v in receipt_info.items():
        setattr(receipt, k, v)
    receipt.save()
    return receipt


def update_msg_notify_by_shop_id(shop_id: int, msg_notify_info: dict):
    """
    更新一个店铺的消息通知设置
    :param shop_id:
    :param msg_notify_info:
    :return:
    """
    msg_notify = get_msg_notify_by_shop_id(shop_id)
    for k, v in msg_notify_info.items():
        setattr(msg_notify, k, v)
    msg_notify.save()
    return msg_notify


def list_msg_notify_fields():
    field_list = []
    for fields in vars(MsgNotify).keys():
        if fields.startswith("_") or fields in ["id", "create_at", "update_at"]:
            continue
        field_list.append(fields)
    return field_list


def get_some_config_by_shop_id(shop_id: int):
    """
    获取商铺的一些奇怪的配置
    :param shop_id:
    :return:
    """
    some_config = SomeConfig.objects.filter(id=shop_id).first()
    if not some_config:
        some_config = create_some_config_by_shop_id(shop_id)
    return some_config


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


def get_share_setup_by_id(shop_id: int):
    """
    通过店铺ID获取店铺的分享信息
    :param shop_id:
    :return:
    """
    share_setup = ShareSetup.objects.filter(id=shop_id).first()
    return share_setup


def get_msg_notify_by_shop_id(shop_id: int):
    """
    获取一个店铺的消息通知设置
    :param shop_id:
    :return:
    """
    msg_notify = MsgNotify.objects.filter(id=shop_id).first()
    if not msg_notify:
        msg_notify = create_msg_notify_by_shop_id(shop_id)
    return msg_notify