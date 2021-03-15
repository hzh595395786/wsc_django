from logs.constant import OrderLogType
from logs.models import OrderLog


def get_order_log_time_by_order_num(order_num: str):
    """
    通过订单号从操作记录获取一个开始订单开始配送时间(订单确认时间)or配送完成时间(订单完成时间)
    :param order_num:
    :return:
    """
    order_log = OrderLog.objects.filter(
        order_num=order_num,
        operate_type__in=[
            [OrderLogType.DIRECT, OrderLogType.CONFIRM, OrderLogType.FINISH]
        ]
    ).order_by("-operate_time").first()
    return order_log.operate_time