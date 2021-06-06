import decimal
import hashlib
import json
import uuid

import requests

from config.services import get_printer_by_shop_id
from customer.models import Customer
from delivery.services import _convert_delivery_period, apply_promotion
from groupon.models import GrouponAttend
from groupon.services import get_shop_groupon_attend_by_id
from logs.constant import OrderLogType
from logs.services import create_order_log
from order.constant import OrderStatus, OrderType, OrderPayType, OrderDeliveryMethod, OrderRefundType, \
    MAP_EVENT_ORDER_TYPE
from order.models import Order, OrderDetail, OrderAddress
from payment.service import payment_query, create_order_transaction, get_order_transaction_by_order_id
from printer.services import print_order
from product.constant import ProductStatus
from product.services import update_product_storage_and_no_record, list_product_by_ids
from promotion.constant import PromotionType
from settings import LCSW_HANDLE_HOST
from shop.services import get_shop_by_shop_id
from storage.constant import ProductStorageRecordType, ProductStorageRecordOperatorType
from storage.services import create_product_storage_records
from user.services import get_pay_channel_by_shop_id
from ws.services import publish_admin
from wsc_django.utils.lcsw import LcswFunds, LcswPay
from customer.services import (
    get_customer_by_customer_id_and_shop_id,
    update_customer_consume_amount_and_point_by_refund,
    update_customer_consume_amount_and_count_and_point_by_consume,
    get_customer_by_user_id_and_shop_id, create_customer
)
from order.selectors import (
    list_order_details_by_order_id,
    get_order_by_shop_id_and_id,
    get_shop_order_by_shop_id_and_id,
    count_abnormal_order,
    get_order_by_customer_id_and_groupon_attend_id
)


######### 订单活动检查相关 #########
_MAP_CHECK_PROMOTION_FUNC = {}


def register_check_promotion(type_):
    def register(func):
        _MAP_CHECK_PROMOTION_FUNC[type_] = func
        return func

    return register


@register_check_promotion(PromotionType.NORMAL)
def _check_normal(**__):
    """普通活动检查"""

    class NormalEvent:
        event_type = 0

    return True, NormalEvent(), {}


@register_check_promotion(PromotionType.GROUPON)
def _check_groupon_attend(
    shop_id: int, customer: Customer, promotion_attend_id: int, **__
):
    """检查拼团活动"""
    success, groupon_attend = get_shop_groupon_attend_by_id(
        shop_id, promotion_attend_id, for_update=True
    )
    if not success:
        return False, groupon_attend, {}
    order_attend = get_order_by_customer_id_and_groupon_attend_id(
        customer.id, promotion_attend_id
    )
    if order_attend:
        return False, "您已经参加过该团", {}

    groupon_attend.event_type = 1

    return True, groupon_attend, {"groupon_attend_id": groupon_attend.id}


######### 订单详情活动检查相关 #########
_MAP_GEN_ORDER_DETAIL_FUNC = {}


def register_gen_order_detail_info(type_):
    def register(func):
        _MAP_GEN_ORDER_DETAIL_FUNC[type_] = func
        return func

    return register


@register_gen_order_detail_info(PromotionType.NORMAL)
def _gen_normal_order_detail_info(item: dict, **__):
    """
    生成普通订单的子订单信息
    :param item: {
                "product": product对象,
                "quantity": quantity,
                "price":price
                "amount":amount
            }
    :param __:
    :return:
    """
    product = item["product"]
    if abs(item["price"] - product.price) > 0.01:
        return False, "商品信息变化，请刷新"
    order_detail_info = {
        "product_id": product.id,
        "quantity_gross": item["quantity"],
        "quantity_net": item["quantity"],
        "price_gross": item["price"],
        "price_net": item["price"],
        "amount_gross": item["amount"],
        "amount_net": item["amount"],
        "promotion_type": 0,
    }
    return True, order_detail_info


@register_gen_order_detail_info(PromotionType.GROUPON)
def _gen_groupon_order_detail_info(
    customer: object, item: dict, promotion_attend: GrouponAttend, **__
):
    """
    生成拼团订单的子订单信息
    :param customer:
    :param item:{
                "product": product对象,
                "quantity": quantity,
                "price":price
                "amount":amount
            }
    :param promotion_attend:
    :param __:
    :return:
    """
    product = item["product"]
    if promotion_attend.groupon.product.id != product.id:
        return False, "拼团商品不匹配，请重新下单"
    # 拼团活动的校验
    success, msg = promotion_attend.limit(customer, item["quantity"])
    if not success:
        return False, msg
    price_net = promotion_attend.calculate()
    if abs(item["price"] - price_net) > 0.01:
        return False, "拼团商品信息有变化，请刷新"
    order_detail_info = {
        "product_id": product.id,
        "quantity_gross": item["quantity"],
        "quantity_net": item["quantity"],
        "price_gross": product.price,
        "price_net": item["price"],
        "amount_gross": product.price * item["quantity"],
        "amount_net": item["amount"],
        "promotion_type": 1,
        "promotion_attend_id": promotion_attend.id,
    }
    return True, order_detail_info


######### 订单相关 #########
def create_order(order_info: dict):
    """
    创建一个订单
    :param order_info:
    :return:
    """
    order = Order(**order_info)
    order.save()
    return order


def _create_order_details(
    order: Order,
    cart_items: list,
    promotion_attend: object = None,
):
    """
    创建订单详情
    :param order:
    :param cart_items:
    :param promotion_attend:
    :return:
    """
    storage_record_list = []
    for item in cart_items:
        # 验证活动,同时生成子订单数据
        gen_order_detail_info_func = _MAP_GEN_ORDER_DETAIL_FUNC.get(
            promotion_attend.event_type, _gen_normal_order_detail_info
        )
        success, order_detail_info = gen_order_detail_info_func(
            customer=order.customer,
            item=item,
            promotion_attend=promotion_attend,
        )
        if not success:
            return False, order_detail_info
        order_detail = create_order_detail(order, order_detail_info)
        # 创建订单详情的过程中更新其优惠前的订单总价
        order.amount_gross += order_detail.amount_gross
        order.total_amount_gross += order_detail.amount_gross
        # 创建订单扣减库存,同时记录库存变更记录
        change_storage = -item["quantity"]
        storage_record = update_product_storage_and_no_record(
            item["product"],
            order.customer.user.id,
            change_storage,
            ProductStorageRecordType.MALL_SALE,
            ProductStorageRecordOperatorType.CUSTOMER,
            order.order_num,
        )
        storage_record_list.append(storage_record)
    storage_record_list = create_product_storage_records(storage_record_list)
    return True, storage_record_list


def create_order_detail(order: Order, order_detail_info: dict):
    """

    :param order:
    :param order_detail_info: {
            "product_id" product.id,
            "quantity_gross": decimal,
            "quantity_net": decimal,
            "price_gross": decimal,
            "price_net": decimal,
            "amount_gross": decimal,
            "amount_net": decimal,
            "promotion_id": groupon.id or null
        }
    :return:
    """
    order_info = {
        "order_id": order.id,
        "shop_id": order.shop.id,
        "customer_id": order.customer.id,
        "create_date": order.create_date,
        "status": order.order_status,
        "pay_type": order.pay_type,
    }
    order_detail_info.update(order_info)
    order_detail = OrderDetail(**order_detail_info)
    order_detail.save()
    return order_detail


def _create_order_address(
        address_info: dict, shop_id: int, delivery_method: int
):
    """
    创建订单地址
    :param address_info:
    :param shop_id:
    :param delivery_method:
    :return:
    """
    order_address = OrderAddress(**address_info)
    # 自提订单更新成店铺地址
    if delivery_method == OrderDeliveryMethod.CUSTOMER_PICK:
        shop = get_shop_by_shop_id(shop_id)
        order_address.province = shop.shop_province
        order_address.city = shop.shop_city
        order_address.county = shop.shop_county
        order_address.address = shop.shop_address
    order_address.save()
    return order_address


def order_data_check(shop_id: int, user_id, args: dict):
    """
    校验订单相关的数据
    :param args:
    :return: order_info
    """
    # 基本参数校验，单个货品的总金额和订单金额的校验
    order_amount = decimal.Decimal(0)
    for item in args["cart_items"]:
        if abs(item["quantity"] * item["price"] - item["amount"]) > 0.01:
            return False, "货品id:{product_id}，价格计算有误".format(product_id=item["product_id"])

        order_amount += item["amount"]
    if abs(order_amount + args["delivery_amount"] - args["total_amount"]) > 0.01:
        return False, "订单金额计算有误"
    # 配送方式关联参数校验
    if args[
        "delivery_method"
    ] == OrderDeliveryMethod.CUSTOMER_PICK and not args.get("delivery_period"):
        return False, "客户自提订单自提时间段必传"
    # 支付方式关联参数校验
    if args["pay_type"] == OrderPayType.WEIXIN_JSAPI and not args.get("wx_openid"):
        return False, "微信支付订单wx_openid必传"
    # 检查客户，如不存在则创建客户
    customer = get_customer_by_user_id_and_shop_id(user_id, shop_id)
    if not customer:
        customer = create_customer(user_id, shop_id)
    # 运费相关校验
    success, delivery_amount_gross = apply_promotion(
        shop_id, args["delivery_method"], order_amount, args["delivery_amount"]
    )
    if not success:
        return False, delivery_amount_gross
    #  处理订单配送方式
    success, delivery_period = _convert_delivery_period(args)
    if not success:
        return False, delivery_period
    # 购物车货品校验
    cart_items = args.get("cart_items")
    product_ids = [item["product_id"] for item in cart_items]
    products = list_product_by_ids(shop_id, product_ids)
    map_products = {product.id: product for product in products}
    for item in cart_items:
        product = map_products.get(item.pop("product_id"))
        if not product:
            return False, "商品已下架, 看看别的商品吧"
        if product.status != ProductStatus.ON:
            return False, "商品已下架, 看看别的商品吧"
        if product.storage < item["quantity"]:
            return (
                False,
                "商品：「{product_name}」库存仅剩 {storage} !".format(product_name=product.name, storage=product.storage)
            )
        item["product"] = product
    # 活动检查
    promotion_type = args["promotion_type"]
    assert promotion_type in _MAP_CHECK_PROMOTION_FUNC.keys()
    check_promotion_func = _MAP_CHECK_PROMOTION_FUNC[promotion_type]
    success, promotion_attend, promotion_attend_field= check_promotion_func(
        shop_id=shop_id,
        customer=customer,
        promotion_attend_id=args["promotion_attend_id"],
    )
    if not success:
        return False, promotion_attend
    order_info = {
        "delivery_method": args["delivery_method"],
        "delivery_period": delivery_period,
        "order_num": str(uuid.uuid1())[:8],  # 临时单号，避免redis自增跳过单号
        "pay_type": args["pay_type"],
        "amount_gross": 0,
        "amount_net": order_amount,
        "delivery_amount_gross": delivery_amount_gross,
        "delivery_amount_net": args["delivery_amount"],
        "total_amount_gross": delivery_amount_gross,
        "total_amount_net": order_amount + args["delivery_amount"],
        "order_type": MAP_EVENT_ORDER_TYPE.get(promotion_type, OrderType.NORMAL),
        "address": args.get("address"),
        "customer_id": customer.id,
        "shop_id": shop_id,
        "promotion_attend": promotion_attend,
    }
    order_info.update(promotion_attend_field)
    if args.get("remark"):
        order_info["remark"] = args.get("remark")
    return True, order_info


def count_paid_order(shop_id: int):
    """
    获取一个店铺未处理(已支付)的订单
    :param shop_id:
    :return:
    """
    count = (
        Order.objects.filter(shop_id=shop_id, order_status=OrderStatus.PAID).count()
    )
    return count


def direct_pay(order: Order):
    """
    直接支付完成流程
    :param order:
    :return:
    """
    set_order_status_paid(order, OrderStatus.PAID)
    # 增加消费额与积分
    update_customer_consume_amount_and_count_and_point_by_consume(
        order.customer.id, order.total_amount_net
    )
    paid_order_count = count_paid_order(order.shop.id)
    publish_admin(order.shop.id, "new_order", {"count": paid_order_count})
    # 订单打印
    printer = get_printer_by_shop_id(order.shop.id)
    if not printer or not printer.auto_print:
        return True, order
    success, order_for_print = get_shop_order_by_shop_id_and_id(order.shop.id, order.id)
    if not success:
        return True, order
    success, _ = print_order(order_for_print, 0)
    if not success:
        return True, order
    return True, order


def cancel_order(shop_id: int, order_id: int):
    """
    取消订单
    :param shop_id:
    :param order_id:
    :return:
    """
    order = get_order_by_shop_id_and_id(shop_id, order_id)
    if not order:
        return False, "订单不存在"
    elif order.order_status != OrderStatus.UNPAID:
        return False, "订单状态已改变"
    elif order.pay_type == OrderPayType.WEIXIN_JSAPI:
        tag, ret_dict = payment_query(order)
        if tag == 2:
            create_order_transaction(
                order.id,
                ret_dict["out_trade_no"],
                ret_dict["total_fee"],
                ret_dict["channel_trade_no"],
            )
            set_order_paid(order)
            return False, "订单已支付, 暂无法取消"

    success, error_obj = set_order_status_canceled(order)
    return success, error_obj


def payment_refund(order: Order):
    """
    订单退款, 直接返回字典
    :param order:
    :return: 字典说明:out_trade_no,out_refund_no必有的；1,+msg;2,+total_fee
    """
    success, pay_channel = get_pay_channel_by_shop_id(order.shop.id)
    if not success:
        return False, pay_channel
    # 先检查一下用户的可用余额是否足够
    query_dict = LcswFunds.queryWithdrawal(pay_channel.smerchant_no)
    # 先全部退
    refund_fee = int(round(order.total_amount_net * 100))
    if query_dict["return_code"] == "01" and query_dict["result_code"] == "01":
        not_settle_amt = int(query_dict["not_settle_amt"])
        if (
                round(not_settle_amt * 1000 / (1000 - pay_channel.clearing_rate))
                < refund_fee
        ):
            return False, "退款失败，当前账户{text}".format(text="余额不足")
    else:
        return (
            False,
            "订单退款外部请求失败: {text}".format(text=query_dict["return_msg"]),
        )
    order_transaction = get_order_transaction_by_order_id(order.id)
    if order_transaction:
        pay_type = "010"
        parameters = LcswPay.getRefundParas(
            pay_type,
            order.order_num,
            order_transaction.transaction_id,
            str(refund_fee),
            pay_channel.smerchant_no,
            pay_channel.terminal_id1,
            pay_channel.access_token,
        )
    else:
        return False, "订单退款外部请求失败: {text}".format(text="找不到交易(SG:no-transaction)")
    try:
        r = requests.post(
            LCSW_HANDLE_HOST + "/pay/100/refund",
            data=json.dumps(parameters),
            verify=False,
            headers={"content-type": "application/json"},
            timeout=(1, 10),
        )
        res_dict = json.loads(r.text)
    except:
        return False, "订单退款外部请求失败: {text}".format(text="退款接口超时或返回异常，请稍后再试(LC)")

    # 响应码：01成功，02失败，响应码仅代表通信状态，不代表业务结果
    if res_dict["return_code"] == "02":
        return False, "订单退款外部请求失败: {text}".format(text=res_dict["return_msg"])
    key_sign = res_dict["key_sign"]
    str_sign = LcswPay.getStrForSignOfRefundRet(res_dict)
    if key_sign != hashlib.md5(str_sign.encode("utf-8")).hexdigest().lower():
        return False, "订单退款外部请求失败: {text}".format(text="签名有误")

    # 业务结果：01成功 02失败
    result_code = res_dict["result_code"]
    if result_code == "02":
        return False, "订单退款外部请求失败: {text}".format(text=res_dict["return_msg"])
    else:
        return True, None


def refund_order(
    shop_id: int, order: Order, refund_type: int, user_id: int = 0
):
    """
    订单退款
    :param shop_id:
    :param order:
    :param refund_type:
    :param user_id:
    :return:
    """
    if (
            order.pay_type == OrderPayType.WEIXIN_JSAPI
            and refund_type == OrderRefundType.WEIXIN_JSAPI_REFUND
    ):
        success, result = payment_refund(order)
        if not success:
            if order.order_type == OrderType.GROUPON and user_id == 0:
                set_order_status_refund_failed(order, user_id, result)
                abnormal_order_count = count_abnormal_order(shop_id)
                publish_admin(
                    shop_id, "abnormal_order", {"count": abnormal_order_count}
                )
            return False, result

    set_order_status_refunded(order, user_id, refund_type)
    return True, None


def set_order_status_refunded(order: Order, user_id: int, refund_type: int):
    """
    将订单设为退款, 对应的子订单也设为退款, 商品库存回退
    :param order:
    :param user_id:
    :param refund_type:
    :return:
    """
    order.order_status = OrderStatus.REFUNDED
    order.refund_type = refund_type
    order_detail_list = list_order_details_by_order_id(order.id)
    order_detail_list.update(order_status=OrderStatus.REFUNDED, refund_type=refund_type)
    storage_record_list = []
    for order_detail in order_detail_list:
        change_storage = order_detail.quantity_net
        storage_record = update_product_storage_and_no_record(
            order_detail.product,
            order_detail.customer.user.id,
            change_storage,
            ProductStorageRecordType.ORDER_CANCEL,
            ProductStorageRecordOperatorType.CUSTOMER,
            order.order_num,
        )
        storage_record_list.append(storage_record)
    create_product_storage_records(storage_record_list)
    # 订单退款,客户积分同时也扣减
    update_customer_consume_amount_and_point_by_refund(
        order.customer.id, order.total_amount_net
    )
    # 生成操作记录
    log_info = {
        "order_id":order.id,
        "order_num": order.order_num,
        "shop_id": order.shop.id,
        "operator_id": user_id,
        "operate_type": OrderLogType.REFUND,
    }
    create_order_log(log_info)
    order.save()


def set_order_paid(order: Order):
    """
    将订单设置为已支付状态,同时生成一些其他的数据
    :param order:
    :return:
    """
    assert order.order_status == OrderStatus.UNPAID

    # 后续订单可能有多种类型
    if order.order_type == OrderType.NORMAL:
        return direct_pay(order)


def set_order_status_paid(order: Order, order_status: int):
    """
    将订单设为支付, status仅为paid, waitting
    :param order:
    :param order_status:
    :return:
    """
    assert order_status in [OrderStatus.PAID, OrderStatus.WAITTING]

    order.order_status = order_status
    order_detail_list = list_order_details_by_order_id(order.id)
    order_detail_list.update(status=order_status)
    order.save()


def set_order_status_canceled(order: Order):
    """
    将订单设为取消, 对应的子订单也设为取消, 商品库存回退
    :param order:
    :return:
    """
    customer = get_customer_by_customer_id_and_shop_id(order.customer.id, order.shop.id)
    order.order_status = OrderStatus.CANCELED
    order_detail_list = list_order_details_by_order_id(order.id)
    order_detail_list.update(order_status=OrderStatus.CANCELED)
    storage_record_list = []
    for order_detail in order_detail_list:
        change_storage = order_detail.quantity_net
        storage_record = update_product_storage_and_no_record(
            order_detail.product,
            customer.user.id,
            change_storage,
            ProductStorageRecordType.ORDER_CANCEL,
            ProductStorageRecordOperatorType.CUSTOMER,
            order.order_num,
        )
        storage_record_list.append(storage_record)
    create_product_storage_records(storage_record_list)
    order.save()
    return True, None


def set_order_status_confirmed_finish(
    order: Order, order_status: int, user_id: int, operate_type: int
):
    """
    将订单的状态设为开始处理, 已完成
    :param order:
    :param order_status:
    :param user_id:
    :param operate_type:
    :return:
    """
    assert order_status in [OrderStatus.CONFIRMED, OrderStatus.FINISHED]

    order.order_status = order_status
    order_detail_list = list_order_details_by_order_id(order.id)
    order_detail_list.update(order_status=order_status)
    # 生成操作记录
    log_info = {
        "order_id": order.id,
        "order_num": order.order_num,
        "shop_id": order.shop.id,
        "operator_id": user_id,
        "operate_type": operate_type,
    }
    create_order_log(log_info)
    order.save()


def set_order_status_refund_failed(
    order: Order, user_id: int, error_text: str
):
    """
    将订单设置为退款失败, 对应的子订单设置为退款失败
    :param order:
    :param user_id:
    :param error_text:
    :return:
    """
    order.order_status = OrderStatus.REFUND_FAIL
    order_detail_list = list_order_details_by_order_id(order.id)
    order_detail_list.update(order_status=OrderStatus.REFUND_FAIL)
    if error_text in [
        "店铺未开通线上支付",
        "店铺支付渠道错误",
    ]:
        operate_content = "支付通道错误"
    elif error_text == "退款失败，当前账户{text}".format(text="余额不足"):
        operate_content = "余额不足"
    else:
        operate_content = "其他"
    log_info = {
        "order_id":order.id,
        "shop_id": order.shop.id,
        "operator_id": user_id,
        "order_num": order.order_num,
        "operate_type": OrderLogType.REFUND_FAIL,
        "operate_content": operate_content,
    }
    create_order_log(log_info)
    order.save()
