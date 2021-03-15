import decimal
import uuid

from django.db.models import Count

from config.services import get_printer_by_shop_id
from customer.models import Customer
from delivery.services import _convert_delivery_period, apply_promotion
from order.constant import OrderStatus, OrderType, OrderPayType, OrderDeliveryMethod
from order.models import Order, OrderDetail, OrderAddress
from payment.service import payment_query, create_order_transaction
from printer.services import print_order
from product.constant import ProductStatus
from product.services import update_product_storage, list_product_by_ids
from shop.models import Shop
from shop.services import get_shop_by_shop_id
from storage.constant import ProductStorageRecordType, ProductStorageRecordOperatorType
from customer.services import (
    get_customer_by_customer_id_and_shop_id,
    update_customer_consume_amount_and_count_and_point_by_consume,
)
from order.selectors import (
    list_order_details_by_order_id,
    get_order_by_shop_id_and_id,
    get_shop_order_by_shop_id_and_id
)


def create_order(shop: Shop, customer: Customer, order_info: dict):
    """
    创建一个订单
    :param shop:
    :param customer:
    :param order_info:
    :return:
    """
    order = Order.objects.create(
        customer=customer, shop=shop, **order_info
    )
    order.save()
    return order


def _create_order_details(
    order: Order,
    cart_items: list,
    customer: Customer,
):
    """
    创建订单详情
    :param order:
    :param cart_items:
    :param customer:
    :return:
    """
    storage_record_list = []
    for item in cart_items:
        success, order_detail_info = _gen_normal_order_detail_info(item)
        if not success:
            return False, order_detail_info
        order_detail = create_order_detail(order, order_detail_info)
        # 创建订单详情的过程中更新其优惠前的订单总价
        order.amount_gross += order_detail.amount_gross
        order.total_amount_gross += order_detail.amount_gross
        # 创建订单扣减库存,同时记录库存变更记录
        change_storage = -item["quantity"]
        storage_record = update_product_storage(
            item["product"],
            customer.user.id,
            change_storage,
            ProductStorageRecordType.MALL_SALE,
            ProductStorageRecordOperatorType.CUSTOMER,
            order.order_num,
        )
        storage_record_list.append(storage_record)
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
    order_detail = OrderDetail.objects.create(**order_detail_info)
    order_detail.save()
    return order_detail


def _gen_normal_order_detail_info(item: dict):
    """
    生成普通订单的子订单信息
    :param item:
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
    order_address = OrderAddress.objects.create(**address_info)
    # 自提订单更新成店铺地址
    if delivery_method == OrderDeliveryMethod.CUSTOMER_PICK:
        shop = get_shop_by_shop_id(shop_id)
        order_address.province = shop.shop_province
        order_address.city = shop.shop_city
        order_address.county = shop.shop_county
        order_address.address = shop.shop_address
    order_address.save()
    return order_address


def order_data_check(shop_id: int, args: dict):
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
        "order_type": OrderType.NORMAL,
    }
    if args.get("remark"):
        order_info["remark"] = args.get("remark")
    return True, order_info


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
    for order_detail in order_detail_list:
        order_detail.order_status = order_status
        order_detail.save()


def count_paid_order(shop_id: int):
    """
    获取一个店铺未处理(已支付)的订单
    :param shop_id:
    :return:
    """
    result = (
        Order.objects.filter(shop_id=shop_id, order_status=OrderStatus.PAID).
        annotate(count=Count("id")).first()
    )
    return result


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
    # publish_admin(order.shop.id, "new_order", {"count": paid_order_count})
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
    elif order.status != OrderStatus.UNPAID:
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


def set_order_status_canceled(order: Order):
    """
    将订单设为取消, 对应的子订单也设为取消, 商品库存回退
    :param order:
    :return:
    """
    customer = get_customer_by_customer_id_and_shop_id(order.customer.id, order.shop.id)
    order.status = OrderStatus.CANCELED
    order_detail_list = list_order_details_by_order_id(order.id)
    for order_detail in order_detail_list:
        order_detail.status = OrderStatus.CANCELED
        order_detail.save()
        change_storage = order_detail.quantity_net
        update_product_storage(
            order_detail.product,
            customer.user.id,
            change_storage,
            ProductStorageRecordType.ORDER_CANCEL,
            ProductStorageRecordOperatorType.CUSTOMER,
            order.order_num,
        )

    return True, None