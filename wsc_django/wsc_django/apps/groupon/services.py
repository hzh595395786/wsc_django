import datetime

from groupon.constant import GrouponStatus
from groupon.models import Groupon
from logs.constant import PromotionLogType
from logs.services import create_promotion_log
from product.services import get_product_by_id


def validate_groupon_period(
    product_id,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    groupon_id: int = 0,
):
    """
    验证拼团时间区间
    :param product_id:
    :param from_datetime:
    :param to_datetime:
    :param groupon_id:
    :return:
    """
    if from_datetime >= to_datetime:
        return False, "结束时间必须大于起始时间"
    elif to_datetime < datetime.datetime.now():
        return False, "结束时间必须大于当前时间"
    elif to_datetime - from_datetime > datetime.timedelta(days=31):
        return False, "最长支持一个月的拼团活动"
    groupons = (
        Groupon.objects.filter(
            product_id=product_id, status=GrouponStatus.ON,
        )
        .exclude(id=groupon_id)
        .all()
    )
    for groupon in groupons:
        periods = [
            from_datetime,
            to_datetime,
            groupon.from_datetime,
            groupon.to_datetime,
        ]
        if (to_datetime - from_datetime) + (
                groupon.to_datetime - groupon.from_datetime
        ) > (
                max(periods) - min(periods)
        ):  # 判断两个区间的重合
            return (
                False,
                "与 {from_datetime} 到 {to_datetime} 的拼团重复".format(
                    from_datetime=groupon.from_datetime, to_datetime=groupon.to_datetime
                ),
            )
    return True, ""


def create_groupon(shop_id: int, user_id: int, args: dict):
    """
    创建拼团活动 user_id仅用于记录日志用
    :param shop_id:
    :param user_id:
    :param args:
    :return:
    """
    product = get_product_by_id(shop_id, args["product_id"], filter_delete=False)
    if not product:
        return False, "货品不存在"
    success, msg = validate_groupon_period(
        args["product_id"], args["from_datetime"], args["to_datetime"]
    )
    if not success:
        return False, msg
    groupon = Groupon.objects.create(
        shop_id=shop_id,
        product_id=args["product_id"],
        price=args["price"],
        from_datetime=args["from_datetime"],
        to_datetime=args["to_datetime"],
        groupon_type=args["groupon_type"],
        success_size=args["success_size"],
        quantity_limit=args["quantity_limit"],
        success_limit=args["success_limit"],
        attend_limit=args["attend_limit"],
        success_valid_hour=args["success_valid_hour"],
        status=GrouponStatus.ON,
    )
    groupon.save()
    # 记录日志
    log_info = {
        "shop_id": shop_id,
        "operator_id": user_id,
        "operate_type": PromotionLogType.ADD_GROUPON,
        "operate_content": product.name,
    }
    create_promotion_log(log_info)
    return True, groupon


def get_shop_groupon_by_id(shop_id: int, groupon_id: int):
    """
    获取一个拼团活动
    :param shop_id:
    :param groupon_id:
    :return:
    """
    groupon = Groupon.objects.filter(shop_id, id=groupon_id).first()
    if not groupon:
        return False, "拼团活动不存在"
    return True, groupon