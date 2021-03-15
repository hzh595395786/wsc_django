import datetime
import decimal

from order.constant import OrderDeliveryMethod
from shop.models import Shop
from delivery.models import DeliveryConfig, PickPeriodConfigLine, Delivery


def create_delivery_config(shop: Shop):
    """
    创建配送设置，所有属性赋默认值
    :param shop: 商铺对象
    :return:
    """
    delivery_config = DeliveryConfig.objects.create(id=shop)
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
    period_line = PickPeriodConfigLine.objects.create(
        delivery_config=delivery_config, from_time=from_time, to_time=to_time
    )
    period_line.save()
    return period_line


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
    if abs(delivery_amount_gross - promotion_amount -delivery_amount_net) > 0.01:
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
