import datetime
from collections import defaultdict

from logs.constant import OrderLogType, MAP_NO_OPERATOR_ORDER_TYPE, OperateLogModule
from logs.models import OrderLog, OperateLogUnify, ConfigLog, PromotionLog, ProductLog, LogBaseModel, StaffLog


def get_all_module_dict():
    module_dict = {}
    for k, v in vars(OperateLogModule).items():
        if not k.startswith("_"):
            module_dict[k] = v
    return module_dict


def  _create_operate_log_unify(log: LogBaseModel):
    """
    在操作记录统一表中创建一条操作记录
    :param log:
    :return:
    """
    log_info = {
        "shop_id": log.shop_id,
        "operator_id": log.operator.id,
        "operate_time": log.operate_time,
        "operate_module": log.operate_module,
        "log_id": log.id,
    }
    operate_log = OperateLogUnify(**log_info)
    operate_log.save()


def create_order_log(log_info: dict):
    """
    创建一个订单操作记录
    :param log_info: {
        "order_id": 1,
        "oder_num": "xxxx",
        "shop_id": 1,
        "operator_id": 1,
        "operate_type": 1,
        "operate_content": ""
    }
    :return:
    """
    order_log = OrderLog(**log_info)
    order_log.save()
    _create_operate_log_unify(order_log)
    return order_log


def create_config_log(log_info: dict):
    """
    创建一条设置模块操作记录
    :param log_info: {
            "shop_id": shop_id,
            "operator_id": user_id,
            "operate_type": ConfigLogType.SHOP_NAME,
            "operate_content": ""
        }
    :return:
    """
    config_log = ConfigLog(**log_info)
    config_log.save()
    _create_operate_log_unify(config_log)
    return config_log


def create_promotion_log(log_info: dict):
    """
    创建一个玩法日志
    :param log_info: {
            "shop_id": shop_id,
            "operator_id": user_id,
            "operate_type": PromotionLogType.ADD_GROUPON,
            "operate_content": groupon_name
        }
    :return:
    """
    promotion_log = PromotionLog(**log_info)
    promotion_log.save()
    _create_operate_log_unify(promotion_log)
    return promotion_log


def create_product_log(log_info: dict):
    """
    创建一条货品板块操作记录
    :param log_info: {
            "shop_id": shop_id,
            "operator_id": user_id,
            "operate_type": ProductLogType.ADD_PRODUCT,
            "operate_content": ""
        }
    :return:
    """
    product_log = ProductLog(**log_info)
    product_log.save()
    _create_operate_log_unify(product_log)
    return product_log


def create_staff_log(log_info: dict):
    """
    创建一条员工操作日志
    :param log_info: {
            "shop_id": shop_id,
            "operator_id": user_id,
            "operate_type": StaffLogType.ADD_STAFF,
            "staff_id": staff_id,
            "operate_content": ""
        }
    :return:
    """
    staff_log = StaffLog(**log_info)
    staff_log.save()
    _create_operate_log_unify(staff_log)
    return staff_log


def get_order_log_time_by_order_num(order_num: str):
    """
    通过订单号从操作记录获取一个开始订单开始配送时间(订单确认时间)or配送完成时间(订单完成时间)
    :param order_num:
    :return:
    """
    order_log = OrderLog.objects.filter(
        order_num=order_num,
        operate_type__in=[
            OrderLogType.DIRECT, OrderLogType.CONFIRM, OrderLogType.FINISH
        ]
    ).order_by("-operate_time").first()
    return order_log.operate_time


def list_order_log_by_shop_id_and_order_num(shop_id: int, order_num: str):
    """
    通过订单号获取一个订单操作记录,带店铺ID版
    :param shop_id:
    :param order_num:
    :return:
    """
    log_list = (
        OrderLog.objects.filter(shop_id=shop_id, order_num=order_num)
        .order_by("-operate_time")
        .all()
    )
    for log in log_list:
        # 自动操作时，操作人id为0
        if not log.operator_id:
            operate_type = MAP_NO_OPERATOR_ORDER_TYPE[log.operate_type]
            log.operate_type = operate_type

    return log_list


def list_one_module_log_by_ids(module_id: int, log_ids: list):
    """
    通过IDS查询一种日志
    :param module_id:
    :param log_ids:
    :return:
    """
    Model = OperateLogUnify.get_operate_log_model(module_id)
    log_list = Model.objects.filter(id__in=log_ids).order_by("id").all()
    return log_list


def list_one_module_log_by_filter(
    shop_id: int,
    module_id: int,
    operator_ids: list,
    from_date: datetime,
    end_date: datetime,
):
    """
    查询一种模块的操作记录
    :param shop_id:
    :param module_id:
    :param operator_ids:
    :param from_date:
    :param end_date:
    :return:
    """
    Model = OperateLogUnify.get_operate_log_model(module_id)
    log_list_query = Model.objects.filter(shop_id=shop_id, operate_time__range=[from_date, end_date])
    if operator_ids:
        log_list_query = log_list_query.filter(operator_id__in=operator_ids)
    log_list_query = log_list_query.order_by("-operate_time")
    log_list = log_list_query.all()
    return log_list


def dict_log_ids_from_operate_log_unify_by_filter(
    shop_id: int,
    module_ids: list,
    operator_ids: list,
    from_date: datetime,
    end_date: datetime,
):
    """
    在统一表中查询所有日志的ID
    :param shop_id:
    :param module_ids:
    :param operator_ids:
    :param from_date:
    :param end_date:
    :return:
    """
    unify_log_list_query = (
        OperateLogUnify.objects.filter(shop_id=shop_id, operate_time__range=[from_date, end_date])
        .exclude(operator_id=0)
    )
    if module_ids:
        unify_log_list_query = unify_log_list_query.filter(
            operate_module__in=module_ids
        )
    if operator_ids:
        unify_log_list_query = unify_log_list_query.filter(
            operator_id__in=operator_ids
        )
    unify_log_list_query = unify_log_list_query.order_by("-operate_time")
    unify_log_list = unify_log_list_query.all()
    unify_log_dict = defaultdict(list)
    for log in unify_log_list:
        unify_log_dict[log.operate_module].append(log.log_id)
    return unify_log_dict


def dict_more_modules_log_by_filter(
    shop_id: int,
    module_ids: list,
    operator_ids: list,
    from_date: datetime,
    end_date: datetime,
):
    """
    查询多种模块的操作记录
    :param shop_id:
    :param module_ids:
    :param operator_ids:
    :param from_date:
    :param end_date:
    :return:
    """
    log_type_2_ids_dict = dict_log_ids_from_operate_log_unify_by_filter(
        shop_id, module_ids, operator_ids, from_date, end_date
    )
    log_type_2_log_list_dict = defaultdict(list)
    for k, v in log_type_2_ids_dict.items():
        log_list = list_one_module_log_by_ids(k, v)
        log_type_2_log_list_dict[k] = log_list
    return log_type_2_log_list_dict