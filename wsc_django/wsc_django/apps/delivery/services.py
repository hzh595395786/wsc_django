from shop.models import Shop
from delivery.models import DeliveryConfig, PickPeriodConfigLine


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