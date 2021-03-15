from customer.services import list_customer_ids_by_user_id
from payment.service import get_wx_jsApi_pay
from product.services import list_product_by_ids, get_product_by_id
from celery_tasks.celery_autowork_task import auto_cancel_order
from celery_tasks.celery_tplmsg_task import OrderCommitTplMsg


def list_product_by_ids_interface(shop_id: int, product_ids: list) -> list:
    """通过ID列出商品"""
    product_list = list_product_by_ids(shop_id, product_ids)

    return product_list


def get_product_by_id_interface(shop_id: int, product_id: int) -> object:
    """通过店铺ID与货品ID获取一个货品"""
    product = get_product_by_id(shop_id, product_id)

    return product


def jsapi_params_interface(order, wx_openid):
    """公众号支付参数获取"""
    return get_wx_jsApi_pay(order, wx_openid)


def auto_cancel_order_interface(shop_id, order_id):
    """超时未支付(15min)自动取消订单"""
    auto_cancel_order.apply_async(args=[shop_id, order_id], countdown=15 * 60)


def order_commit_tplmsg_interface(order_id: int) -> None:
    """发送订单提交成功模板消息"""
    OrderCommitTplMsg.send(order_id=order_id)


def list_customer_ids_by_user_id_interface(user_id: int) -> list:
    """通过user_id获取一个人所有的客户信息"""
    customer_ids = list_customer_ids_by_user_id(user_id)
    return customer_ids