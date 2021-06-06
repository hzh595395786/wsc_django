import copy
import datetime
import decimal

from logs.constant import OrderLogType
from logs.services import create_order_log
from order.constant import OrderDeliveryMethod
from shop.models import Shop
from delivery.models import DeliveryConfig, PickPeriodConfigLine, Delivery


def create_delivery_config(shop_id: int):
    """
    创建配送设置，所有属性赋默认值
    :param shop_id: 商铺id
    :return:
    """
    delivery_config = DeliveryConfig(id=shop_id)
    delivery_config.save()
    return delivery_config


def create_pick_period_line(
        delivery_config: DeliveryConfig, from_time: str, to_time: str
    ):
    """
    创建自提时间段
    :param delivery_config: 配送设置对象
    :param from_time:自提起始时间
    :param to_time:自提终止时间
    :return:
    """
    period_line = PickPeriodConfigLine(
        delivery_config=delivery_config, from_time=from_time, to_time=to_time
    )
    period_line.save()
    return period_line


def create_pick_period_lines(
    delivery_config: DeliveryConfig, pick_period_lines: list
):
    """
    批量创建自提时间段
    :param delivery_config:
    :param pick_period_lines: [
                {"from_time":'xx', "to_time":'xx'},
                {"from_time":'xx', "to_time":'xx'},
            ]
    :return:
    """
    period_line_list = []
    for pick_period_line in pick_period_lines:
        period_line = PickPeriodConfigLine(
            delivery_config=delivery_config,
            from_time=pick_period_line["from_time"],
            to_time=pick_period_line["to_time"]
        )
        period_line_list.append(period_line)
    PickPeriodConfigLine.objects.bulk_create(period_line_list)


def create_order_delivery(delivery_info: dict):
    """
    创建一个订单配送记录
    :param delivery_info:
    :return:
    """
    delivery = Delivery(**delivery_info)
    delivery.save()
    return delivery


def update_delivery_config(shop_id: int, args: dict, user_id: int = 0):
    """
    更新配送设置
    :param shop_id:
    :param args:
    :param user_id:
    :return:
    """
    success, delivery_config = get_delivery_config_by_shop_id(shop_id)
    if not success:
        return False, delivery_config
    old_delivery_config = copy.deepcopy(delivery_config)
    if args.get("pick_periods"):
        # 删除原有的所有时间
        delivery_config.pick_periods.delete()
        # 添加新的配送时间
        create_pick_period_lines(
            delivery_config, args["pick_periods"]
        )
    # 更新配送设置主表字段
    for k, v in args.items():
        setattr(delivery_config, k, v)
    delivery_config.save()
    # 店铺至少开启一种配送方式
    if not delivery_config.home_on and not delivery_config.pick_on:
        return False, "店铺至少需要开启一种配送方式"
    # 创建操作记录,user_id为0时为点击配送/自提按钮,无需记录操作日志
    if user_id:
        for k, v in args.items():
            operate_type = getattr(OrderLogType, k.upper(), None)
            if operate_type is None:
                continue
            old_value = round(float(getattr(old_delivery_config, k)), 2)
            new_value = round(float(v), 2)
            if old_value != new_value:
                log_info = {
                    "shop_id": shop_id,
                    "operator_id": user_id,
                    "order_num": "0",
                    "order_id": "0",
                    "operate_type": operate_type,
                    "operate_content": "{}|{}".format(old_value, new_value),
                }
                create_order_log(log_info)
    return success, ""


def get_delivery_config_by_shop_id(shop_id: int):
    """
    通过店铺id获取商铺配送设置
    :param shop_id:
    :return:
    """
    delivery_config = DeliveryConfig.objects.filter(id=shop_id).first()
    if not delivery_config:
        return False, "店铺配送设置不存在"
    pick_periods = list_pick_peirods_by_delivery_config_id(delivery_config.id)
    delivery_config.pick_periods = pick_periods
    return True, delivery_config


def list_pick_peirods_by_delivery_config_id(delivery_config_id: int):
    """
    通过配送设置id获取自提时间设置
    :param delivery_config_id:
    :return:
    """
    pick_peirods_list = (
        PickPeriodConfigLine.objects.filter(delivery_config_id=delivery_config_id).
        order_by("from_time").
        all()
    )
    return pick_peirods_list


def apply_promotion(
    shop_id: int,
    delivery_method: int,
    order_amount: decimal.Decimal,
    delivery_amount_net: decimal.Decimal,
):
    """
    校验订单的配送优惠，并返回获取订单配送优惠前金额
    :param shop_id:
    :param delivery_method:
    :param order_amount:
    :param delivery_amount_net:
    :return:
    """
    success, delivery_config = get_delivery_config_by_shop_id(shop_id)
    if not success:
        return False, delivery_config
    is_valid = delivery_config.is_delivery_method_valid(delivery_method)
    if not is_valid:
        return False, "配送方式无效，请重新选择或刷新页面后重试"
    is_occupied = delivery_config.limit(delivery_method, order_amount)
    if not is_occupied:
        return False, "订单未到起送价"
    promotion_amount = delivery_config.calculate(delivery_method, order_amount)
    delivery_amount_gross = delivery_config.get_delivery_amount_gross(delivery_method)
    if abs(delivery_amount_gross - promotion_amount - delivery_amount_net) > 0.01:
        return False, "订单运费计算有误"
    return True, delivery_amount_gross


def _convert_delivery_period(args: dict):
    """
    订单配送时间段处理
    :param args:
    :return:
    """
    if args["delivery_method"] == OrderDeliveryMethod.HOME_DELIVERY:
        delivery_period = "立即配送"
    else:
        try:
            day, period = args["delivery_period"].split(" ")
        except ValueError:
            return False, "配送日期参数错误"

        if day == "今天":
            day_converted = datetime.date.today().strftime("%Y-%m-%d")
        elif day == "明天":
            day_converted = (datetime.date.today() + datetime.timedelta(1)).strftime(
                "%Y-%m-%d"
            )
        else:
            return False, "配送日期参数错误"
        delivery_period = "{day_converted} {period}".format(
            day_converted=day_converted, period=period
        )

    return True, delivery_period


def get_order_delivery_by_delivery_id(delivery_id: int):
    """
    获取一个订单的配送记录,仅商家送货有
    :param delivery_id:
    :return:
    """
    delivery = Delivery.objects.filter(id=delivery_id).first()
    return delivery
