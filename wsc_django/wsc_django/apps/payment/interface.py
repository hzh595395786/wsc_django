from order.models import Order
from order.services import set_order_paid
from user.services import get_openid_by_user_id_and_appid, create_user_openid


def get_user_openid_interface(user_id: int, mp_appid: str):
    """通过用户id和公众号的mp_appid获取用户的wx_openid"""
    return get_openid_by_user_id_and_appid(user_id, mp_appid)


def create_user_openid_interface(user_id: int, mp_appid: str, wx_openid: str):
    """创建用户openID """
    return create_user_openid(user_id, mp_appid, wx_openid)


def pay_order_interfaces(order: Order):
    """将订单设置为已支付状态,同时生成一些其他的数据, 带commit"""
    return set_order_paid(order)