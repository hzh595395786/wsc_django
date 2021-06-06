import datetime

from django.utils.timezone import make_aware

from customer.models import Customer
from customer.services import get_customer_by_user_id_and_shop_id, create_customer
from groupon.constant import GrouponStatus, GrouponAttendStatus, GrouponAttendLineStatus
from groupon.models import Groupon, GrouponAttend, GrouponAttendDetail
from logs.constant import PromotionLogType
from logs.services import create_promotion_log
from product.constant import ProductStatus
from product.models import Product
from product.services import get_product_by_id, list_product_by_filter
from promotion.services import stop_product_promotion


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
            make_aware(from_datetime),
            make_aware(to_datetime),
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


def launch_groupon_attend(shop_id: int, user_id: int, groupon_id: int):
    """
    验证待开团拼团活动
    :param shop_id:
    :param user_id:
    :param groupon_id:
    :return:
    """
    success, groupon = get_shop_groupon_by_id(shop_id, groupon_id)
    if not success:
        return False, groupon
    elif groupon.status != GrouponStatus.ON:
        return False, "活动已结束, 看看其他商品吧"
    elif groupon.to_datetime <= datetime.datetime.now():
        return False, "活动已结束, 看看其他商品吧"
    elif groupon.from_datetime > datetime.datetime.now():
        return False, "活动已结束, 看看其他商品吧"
    customer = get_customer_by_user_id_and_shop_id(user_id, shop_id)
    if not customer:
        customer = create_customer(user_id, shop_id)
    valid_datetime = datetime.datetime.now() + datetime.timedelta(
        hours=groupon.success_valid_hour
    )
    groupon_attend = GrouponAttend(
        groupon=groupon,
        size=0,
        success_size=groupon.success_size,
        to_datetime=min(groupon.to_datetime, valid_datetime),
        status=GrouponAttendStatus.CREATED,
    )
    groupon_attend.save()
    attend_detail = _create_groupon_attend_detail(
        groupon_attend, customer, is_sponsor=True
    )
    # 拼团参与校验
    groupon_attend.sponsor_detail = attend_detail
    success, msg = groupon_attend.limit(customer, 0)
    if not success:
        return False, msg
    # 一旦开团，无法再进行编辑
    if groupon.is_editable:
        groupon.set_uneditable()
        groupon.save()
    return True, groupon_attend


def _create_groupon_attend_detail(
    groupon_attend: GrouponAttend,
    customer: Customer,
    is_sponsor: bool=False,
):
    """
    创建拼团参与详情
    :param groupon_attend:
    :param customer:
    :param is_sponsor:
    :return:
    """
    groupon_attend_detail = GrouponAttendDetail(
        groupon_attend=groupon_attend,
        customer=customer,
        is_sponsor=is_sponsor,
        is_new_customer=customer.is_new_customer(),
        status=GrouponAttendLineStatus.UNPAID,
    )
    groupon_attend_detail.save()
    return groupon_attend_detail


def create_groupon(
        shop_id: int, user_id: int, product: Product, args: dict
):
    """
    创建拼团活动 user_id仅用于记录日志用
    :param shop_id:
    :param user_id:
    :param product:
    :param args:
    :return:
    """
    groupon = Groupon(
        shop_id=shop_id,
        product_id=product.id,
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
    return groupon


def update_groupon(
    shop_id: int, user_id: int, product: Product, groupon: Groupon, args: dict
):
    """
    编辑拼团活动 user_id仅用于记录日志
    :param shop_id:
    :param user_id:
    :param product:
    :param groupon:
    :param args:
    :return:
    """
    for k, v in args.items():
        setattr(groupon, k ,v)
    # 拼团编辑后直接上线
    groupon.status = GrouponStatus.ON
    groupon.save()
    # 记录日志
    log_info = {
        "shop_id": shop_id,
        "operator_id": user_id,
        "operate_type": PromotionLogType.UPDATE_GROUPON,
        "operate_content": product.name,
    }
    create_promotion_log(log_info)
    return groupon


def set_groupon_off(shop_id: int, user_id: int, groupon_id: int, force=False):
    """
    停用一个拼团
    :param shop_id:
    :param user_id:
    :param groupon_id:
    :param force:
    :return:
    """
    success, groupon = get_shop_groupon_by_id(shop_id, groupon_id)
    if not success:
        return False, groupon
    elif groupon.status == GrouponStatus.EXPIRED:
        return False, "拼团活动已过期，请重新编辑"
    groupon.status = GrouponStatus.OFF
    groupon.save()
    if (
        groupon.from_datetime <= make_aware(datetime.datetime.now())
        and groupon.to_datetime >= make_aware(datetime.datetime.now())
    ):
        stop_product_promotion(shop_id, groupon.product_id)
    # 记录日志
    product = get_product_by_id(
        shop_id, groupon.product_id, filter_delete=False
    )
    log_info = {
        "shop_id": shop_id,
        "operator_id": user_id,
        "operate_type": PromotionLogType.STOP_GROUPON,
        "operate_content": product.name,
    }
    create_promotion_log(log_info)
    return True, groupon


def force_success_groupon_attend(shop_id: int, groupon_attend_id: int):
    """
    强制成团
    :param shop_id:
    :param groupon_attend_id:
    :return:
    """
    success, groupon_attend = get_shop_groupon_attend_by_id(
        shop_id, groupon_attend_id, for_update=True
    )
    if not success:
        return False, groupon_attend
    elif groupon_attend.status != GrouponAttendStatus.WAITTING:
        return False, "团状态错误, 无法强制成团"
    elif groupon_attend.size >= groupon_attend.success_size:
        return False, "拼团已经满员, 无法强制成团, 请等待团员完成支付"
    unpaid_details = list_unpaid_details_by_groupon_attend_id(groupon_attend_id)
    if unpaid_details:
        return False, "还有团员未支付, 无法强制成团, 请等待团员完成支付"
    groupon_attend.anonymous_size = groupon_attend.success_size - groupon_attend.size
    groupon_attend.size = groupon_attend.success_size
    groupon_attend.save()
    return True, groupon_attend


def get_shop_groupon_by_id(shop_id: int, groupon_id: int):
    """
    获取一个拼团活动
    :param shop_id:
    :param groupon_id:
    :return:
    """
    groupon = Groupon.objects.filter(shop_id=shop_id, id=groupon_id).first()
    if not groupon:
        return False, "拼团活动不存在"
    return True, groupon


def get_groupon_by_id(shop_id: int, groupon_id: int):
    """
    不返回错误
    :param shop_id:
    :param groupon_id:
    :return:
    """
    groupon = Groupon.objects.filter(shop_id=shop_id, id=groupon_id).first()
    return groupon


def get_shop_groupon_attend_by_id(
    shop_id: int, groupon_attend_id: int, for_update: bool = False
):
    """
    通过id获取一个拼团参与，并附带拼团活动的信息和团长的信息
    :param shop_id:
    :param groupon_attend_id:
    :param for_update: 是否用于更新，为True时加排它锁
    :return:
    """
    if for_update:
        groupon_attend = (
            GrouponAttend.objects.select_for_update().get(id=groupon_attend_id).first()
        )
    else:
        groupon_attend = GrouponAttend.objects.filter(id=groupon_attend_id).first()
    if not groupon_attend:
        return False, "团不存在"
    groupon = Groupon.objects.filter(shop_id=shop_id, id=groupon_attend.groupon.id).first()
    if not groupon:
        return False, "拼团活动不存在"
    sponsor_detail = (
        GrouponAttendDetail.objects.filter(
            groupon_attend_id=groupon_attend_id, is_sponsor=True
        )
        .first()
    )
    if not sponsor_detail:
        return False, "团长不存在"
    groupon_attend.sponsor_detail = sponsor_detail
    return True, groupon_attend


def list_shop_groupons(shop_id: int, args: dict):
    """
    获取拼团活动列表
    :param shop_id:
    :param args:
    :return:
    """
    groupons = Groupon.objects.filter(
        shop_id=shop_id, status__in=[GrouponStatus.ON, GrouponStatus.OFF, GrouponStatus.EXPIRED]
    )
    # 货品名搜索
    if args["product_name"]:
        states = [ProductStatus.ON, ProductStatus.OFF, ProductStatus.DELETED]
        group_id = 0
        products = list_product_by_filter(shop_id, states, args["product_name"], group_id)
        product_ids = [p.id for p in products]
        groupons = groupons.filter(product_id__in=product_ids)
    groupons = groupons.order_by("status", "-id").all()
    return groupons


def list_waitting_groupon_attends(shop_id: int, groupon_id: int):
    """
    列出拼团中的团
    :param shop_id:
    :param groupon_id:
    :return:
    """
    success, groupon = get_shop_groupon_by_id(shop_id, groupon_id)
    if not success:
        return False, groupon
    groupon_attends = (
        GrouponAttend.objects.filter(
            groupon_id=groupon_id, status=GrouponAttendStatus.WAITTING
        )
        .all()
    )
    # 拼团参与详情
    groupon_attend_ids = [g.id for g in groupon_attends]
    groupon_attend_details = (
        GrouponAttendDetail.objects.filter(
            groupon_attend_id__in=groupon_attend_ids,
            is_sponsor=True,
            status=GrouponAttendLineStatus.PAID
        )
        .all()
    )
    map_attend_customer = {
        l.groupon_attend_id: l.customer for l in groupon_attend_details
    }
    # 为拼团参与赋团长
    for groupon_attend in groupon_attends:
        sponsor = map_attend_customer[groupon_attend.id]
        groupon_attend.sponsor = sponsor
    return True, groupon_attends


def list_paid_details_by_groupon_attend_id(groupon_attend_id: int):
    """
    列出一个拼团参与所有已支付的详情
    :param groupon_attend_id:
    :return:
    """
    paid_details = GrouponAttendDetail.objects.filter(
        groupon_attend_id=groupon_attend_id, status=GrouponAttendLineStatus.PAID
    ).all()
    return paid_details


def list_unpaid_details_by_groupon_attend_id(groupon_attend_id: int):
    """
    列出一个拼团参与未支付的所有详情
    :param groupon_attend_id:
    :return:
    """
    unpaid_details = GrouponAttendDetail.objects.filter(
        groupon_attend_id=groupon_attend_id, status=GrouponAttendLineStatus.UNPAID
    ).all()
    return unpaid_details


def list_created_groupon_attends_by_groupon_id(groupon_id: int):
    """
    列出已创建的团
    :param groupon_id:
    :return:
    """
    groupon_attends = GrouponAttend.objects.filter(
        groupon_id=groupon_id, status=GrouponAttendStatus.CREATED
    ).all()
    return groupon_attends


def list_groupon_attends_by_groupon(
    groupon: Groupon, states: list,
):
    """
    通过拼团活动id获取拼团参与
    :param groupon:
    :param states:
    :return:
    """
    if not states:
        return []
    groupon_attends = GrouponAttend.objects.filter(
        groupon_id=groupon.id, status__in=states
    )
    groupon_attends = groupon_attends.all()
    # 拼团参与详情
    groupon_attend_ids = [g.id for g in groupon_attends]
    groupon_attend_details = (
        GrouponAttendDetail.objects.filter(
            groupon_attend_id__in=groupon_attend_ids,
            status=GrouponAttendLineStatus.PAID,
            is_sponsor=True,
        ).all()
    )
    map_attend_customer = {
        l.groupon_attend_id: l.customer_id for l in groupon_attend_details
    }
    # 为拼团参与赋团长
    for groupon_attend in groupon_attends:
        sponsor = map_attend_customer[groupon_attend.id]
        groupon_attend.sponsor = sponsor
    return groupon_attends


def list_alive_groupon_by_product_ids(product_ids: list):
    """
    查询此刻或者未来有拼团活动的货品id的集合
    :param product_ids:
    :return:
    """
    groupon_list = Groupon.objects.filter(
        product_id__in=product_ids,
        status=GrouponStatus.ON,
        to_datetime__gte=make_aware(datetime.datetime.now())
    ).all()
    groupon_product_set = {groupon.product_id for groupon in groupon_list}
    return groupon_product_set


def count_groupon_attend_by_groupon_id_and_customer_id(
    groupon_id: int, customer_id: int
):
    """
    计算一个人某个拼团的参与次数
    :param groupon_id:
    :param customer_id:
    :return:
    """
    total_attend_count = (
        GrouponAttendDetail.objects.filter(
            groupon_attend__groupon_id=groupon_id,
            groupon_attend__status__in=[
                GrouponAttendStatus.WAITTING, GrouponAttendStatus.SUCCEEDED
            ],
            customer_id=customer_id,
            status__in=[GrouponAttendLineStatus.PAID, GrouponAttendLineStatus.UNPAID]
        )
        .count()
    )
    return total_attend_count