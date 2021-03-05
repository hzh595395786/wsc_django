from django.db.models import Q

from customer.models import Customer, CustomerPoint
from user.constant import USER_OUTPUT_CONSTANT
from user.services import get_user_by_id


def create_customer(user_id: int, shop_id: int):
    """
    创建客户
    :param user_id:
    :param shop_id:
    :return:
    """
    customer = Customer.objects.create(shop_id=shop_id, user_id=user_id)
    customer.save()
    return customer


def update_customer_remark(customer: Customer, remark: str):
    """
    更改客户备注
    :param customer:
    :param remark:
    :return:
    """
    customer.remark = remark
    customer.save()
    return True, ""


def get_customer_by_user_id_and_shop_id(user_id: int, shop_id: int):
    """
    通过店铺ID和userID查到一个客户
    :param user_id:
    :return:
    """
    customer = Customer.objects.filter(user_id=user_id, shop_id=shop_id).first()
    return customer


def get_customer_by_customer_id_and_shop_id(
        customer_id: int,
        shop_id: int,
):
    """
    通过客户id和商铺id查询单个客户信息,包括详情
    :param customer_id:
    :param shop_id:
    :return:
    """
    customer = Customer.objects.filter(shop_id=shop_id, id=customer_id).first()
    return customer


def list_customer_by_shop_id(
        shop_id: int,
        sort_prop: str,
        sort: str,
        keyword: str,
):
    """
    获取一个店铺的客户列表
    :param shop_id:
    :param sort_prop:
    :param sort:
    :param keyword:
    :return:
    """
    customer_user_query = Customer.objects.filter(shop_id=shop_id)
    if keyword:
        customer_user_query = customer_user_query.filter(
            Q(user__nickname__contains=keyword) |
            Q(user__phone__contains=keyword)
        )
    if sort and sort_prop:
        order_by = sort_prop
        if sort == "desc":
            order_by = "-{}".format(sort_prop)
        customer_user_query = customer_user_query.order_by(order_by)
    customer_user_list = customer_user_query.all()
    return customer_user_list


def list_customer_point_by_customer_id(customer_id: int):
    """
    查看一个客户的历史积分记录
    :param customer_id:
    :return:
    """
    customer_point_list_query = (
        CustomerPoint.objects.filter(customer_id=customer_id).
        order_by("-create_time", "-id")
    )
    customer_point_list = customer_point_list_query.all()
    return customer_point_list
