import decimal

from django.db.models import Q

from customer.constant import MineAddressStatus, MineAddressDefault, CustomerPointType
from customer.models import Customer, CustomerPoint, MineAddress


#####################顾客相关#####################
from user.constant import USER_OUTPUT_CONSTANT


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


def update_customer_consume_amount_and_count_and_point_by_consume(
    customer_id: int, consume_amount: decimal
):
    """
    根据订单记录的客户ID更新客户的消费总额与消费次数与积分
    :param customer_id:
    :param consume_amount:
    :return:
    """
    customer = get_customer_by_customer_id(customer_id)
    # 积分四舍五入
    point = round(consume_amount)
    # 客户首单, 积5分
    if customer.consume_count == 0:
        customer.point += decimal.Decimal(5)
        create_customer_point(
            customer.id,
            customer.point,
            decimal.Decimal(5),
            CustomerPointType.FIRST,
        )
        customer.save()
    customer.consume_amount += consume_amount
    customer.consume_count += 1
    customer.point += point
    customer.save()
    create_customer_point(
        customer.id, customer.point, point, CustomerPointType.CONSUME
    )


def update_customer_consume_amount_and_point_by_refund(
    customer_id: int, consume_amount: decimal
):
    """
    退款时,退消费总额,退积分,不退消费次数
    :param customer_id:
    :param consume_amount:
    :return:
    """
    customer = get_customer_by_customer_id(customer_id)
    # 积分四舍五入
    point = round(consume_amount)
    # # 退首单,相应的退掉首单的积分
    # if customer.consume_count == 1:
    #     point += decimal.Decimal(5)
    customer.consume_amount -= consume_amount
    customer.point -= point
    customer.save()
    create_customer_point(
        customer.id, customer.point, -point, CustomerPointType.REFUND
    )


def get_customer_by_customer_id(customer_id: int):
    """
    通过客户ID查询客户
    :param customer_id:
    :return:
    """
    customer = Customer.objects.filter(id=customer_id).first()
    return customer


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
        with_user_info: bool = False
):
    """
    通过客户id和商铺id查询单个客户信息,包括详情
    :param customer_id:
    :param shop_id:
    :param with_user_info: 带上用户信息
    :return:
    """
    customer = Customer.objects.filter(shop_id=shop_id, id=customer_id).first()
    if customer and with_user_info:
        for key in USER_OUTPUT_CONSTANT:
            setattr(customer, key, getattr(customer.user, key))
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
    customer_list_query = Customer.objects.filter(shop_id=shop_id)
    if keyword:
        customer_list_query = customer_list_query.filter(
            Q(user__nickname__contains=keyword) |
            Q(user__phone__contains=keyword)
        )
    if sort and sort_prop:
        order_by = sort_prop
        if sort == "desc":
            order_by = "-{}".format(sort_prop)
    else:
        order_by = "create_date"
    customer_list_query = customer_list_query.order_by(order_by)
    customer_list = customer_list_query.all()
    for customer in customer_list:
        for _ in USER_OUTPUT_CONSTANT:
            setattr(customer, _ , getattr(customer.user, _))
    return customer_list


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


def list_customer_ids_by_user_id(user_id: int):
    """
    通过user_id获取一个人的所有客户ID
    :param user_id:
    :return:
    """
    customer_list = Customer.objects.filter(user_id=user_id).all()
    customer_ids = [ c.id for c in customer_list]
    return customer_ids


#####################积分相关#####################
def create_customer_point(
    customer_id: int, current_point: decimal, point_change: decimal, type: int
):
    customer_point = CustomerPoint.objects.create(
        customer_id=customer_id, current_point=current_point, point_change=point_change, type=type
    )
    customer_point.save()
    return customer_point


#####################地址相关#####################
def create_mine_address(address_info: dict, user_id: int, shop_id: int):
    """
    创建一个地址
    :param address_info: {
        "name": "name",
        "sex": "1",
        "province": 420000,
        "city": 420100,
        "county": 420111,
        "address": "光谷智慧谷一栋505",
        "longitude": "90",
        "latitude": "45",
        "phone": "152xxxxxxxx",
        "default": 1
    }
    :param user_id:
    :param shop_id:
    :return:
    """
    mine_address = MineAddress.objects.create(user_id=user_id, shop_id=shop_id, **address_info)
    mine_address.save()
    return mine_address


def delete_mine_address_by_id(address_id: int, user_id: int, shop_id: int):
    """
    根据address_id列表,user_id和shop_id删除我的地址
    :param address_id:
    :param user_id:
    :param shop_id:
    :return:
    """
    mine_address = get_mine_address_by_id(address_id, user_id, shop_id)
    if not mine_address:
        return False, "地址不存在"
    mine_address.status = MineAddressStatus.DELETE
    mine_address.save()
    return True, ""


def get_mine_address_by_id(address_id: int, user_id: int, shop_id: int):
    """
    通过user_id,shop_id和id获取一个地址对象
    :param address_id:
    :param shop_id:
    :param user_id:
    :return:
    """
    mine_address = MineAddress.objects.filter(id=address_id, shop_id=shop_id, user_id=user_id).first()
    return mine_address


def list_mine_address_by_user_id_and_shop_id(user_id: int, shop_id: list, filter_delete: bool = True):
    """
    通过user_id和shop_id获取我的地址列表
    :param user_id:
    :param shop_id:
    :return:
    """
    mine_address_list_query = MineAddress.objects.filter(user_id=user_id, shop_id=shop_id)
    if filter_delete:
        mine_address_list_query.exclude(status=MineAddressStatus.DELETE)
    mine_address_list_query = mine_address_list_query.order_by("-create_at", "-id")
    mine_address_list = mine_address_list_query.all()
    return mine_address_list


def get_mine_default_address_by_user_id_and_shop_id(user_id: int, shop_id: int):
    """
    通过user_id和shop_id找到客户的默认地址
    :param user_id:
    :param shop_id:
    :return:
    """
    default_address = MineAddress.objects.filter(
        user_id=user_id, shop_id=shop_id, default=MineAddressDefault.YES
    ).first()
    return default_address
