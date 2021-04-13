import datetime

from groupon.models import Groupon
from celery_tasks.celery_autowork_task import auto_publish_groupon, auto_expire_groupon


def publish_gruopon_interface(groupon: Groupon):
    """
    根据拼团开始时间发布拼团
    :param groupon:
    :return:
    """
    countdown = (groupon.from_datetime - datetime.datetime.now()).total_seconds()
    # 当前时间以前的拼团直接发布，当前时间以后的拼团直接发布
    auto_publish_groupon.apply_async(
        args=[groupon.shop.id, groupon.id],
        countdown=int(countdown) if countdown > 0 else 0,
    )


def expire_groupon_interface(groupon: Groupon):
    """
    根据拼团结束时间过期拼团
    :param groupon:
    :return:
    """
    countdown = (groupon.to_datetime - datetime.datetime.now()).total_seconds()
    auto_expire_groupon.apply_async(
        args=[groupon.shop.id, groupon.id],
        countdown=int(countdown) if countdown > 0 else 0,
    )
