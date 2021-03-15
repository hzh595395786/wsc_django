import decimal

from rest_framework import status
from webargs import fields, validate
from webargs.djangoparser import use_args

from order.constant import OrderDeliveryMethod, OrderPayType, OrderType
from order.interface import (
    list_product_by_ids_interface,
    get_product_by_id_interface,
    jsapi_params_interface,
    auto_cancel_order_interface,
    order_commit_tplmsg_interface,
    list_customer_ids_by_user_id_interface,
)
from order.services import order_data_check, set_order_paid
from order.selectors import get_customer_order_with_detail_by_id
from product.constant import ProductStatus
from user.constant import Sex
from wsc_django.utils.views import MallBaseView
from order.serializers import (
    MallOrderCreateSerializer,
    MallOrderSerializer
)


class MallOrderView(MallBaseView):
    """商城端-提交订单"""

    @use_args(
        {
            "cart_items": fields.Nested(
                {
                    "product_id": fields.Integer(required=True, comment="货品ID"),
                    "quantity": fields.Decimal(required=True, comment="货品下单量"),
                    "price": fields.Decimal(required=True, comment="货品单价"),
                    "amount": fields.Decimal(required=True, comment="货品总金额"),
                },
                required=True,
                validate=[validate.Length(1)],
                many=True,
                unknown=True,
                comment="订单货品详情",
            ),
            "delivery_amount": fields.Decimal(required=True, comment="订单运费"),
            "total_amount": fields.Decimal(required=True, comment="订单总金额"),
            "address": fields.Nested(
                {
                    "name": fields.String(required=True, comment="收货人姓名"),
                    "phone": fields.String(required=True, comment="收货人手机号"),
                    "sex": fields.Integer(
                        required=True,
                        validate=[validate.OneOf([Sex.UNKNOWN, Sex.MALE, Sex.FEMALE])],
                        comment="性别",
                    ),
                    "address": fields.String(required=True, comment="详细地址"),
                    "province": fields.Integer(required=True, comment="省编码"),
                    "city": fields.Integer(required=True, comment="市编码"),
                    "county": fields.Integer(required=True, comment="区编码"),
                },
                required=True,
                unknown=True,
                comment="订单地址",
            ),
            "delivery_method": fields.Integer(
                required=True,
                validate=validate.OneOf(
                    [
                        OrderDeliveryMethod.HOME_DELIVERY,
                        OrderDeliveryMethod.CUSTOMER_PICK,
                    ]
                ),
                comment="配送方式：1：送货上门，2：客户自提",
            ),
            "delivery_period": fields.String(comment="自提时间段（仅自提必传），举例：今天 12:00~13:00"),
            "pay_type": fields.Integer(
                required=True,
                validate=validate.OneOf(
                    [OrderPayType.WEIXIN_JSAPI, OrderPayType.ON_DELIVERY]
                ),
                comment="支付方式：1：微信支付，2：货到付款",
            ),
            "wx_openid": fields.String(comment="微信支付openid"),
            "remark": fields.String(validate=validate.Length(0, 30), comment="订单备注"),
        },
        location="json",
    )
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        shop_id = self.current_shop.id
        # 订单数据校验
        success, order_info = order_data_check(shop_id, args)
        if not success:
            return self.send_fail(error_text=order_info)
        order_info["address"] = args.get("address")
        data = {
            "order_info": order_info,
        }
        serializer = MallOrderCreateSerializer(
            data=data, context={"self": self, "cart_items": args.get("cart_items")}
        )
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        order = serializer.save()
        if order.pay_type == OrderPayType.WEIXIN_JSAPI:
            success, params = jsapi_params_interface(
                order, args["wx_openid"]
            )
            if not success:
                return self.send_fail(error_obj=params)
            auto_cancel_order_interface(order.shop_id, order.id)
            return self.send_success(data=params, order_id=order.id)
        else:
            set_order_paid(order)
            # 订单提交成功微信提醒, 暂时只有普通订单才发送消息,且页面没有控制按钮
            if order.order_type == OrderType.NORMAL:
                # 测试省略
                pass
                # order_commit_tplmsg_interface(order.id)
            return self.send_success(order_id=order.id)

    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            )
        },
        location="query"
    )
    def get(self, request, args, shop_code):
        customer_ids = list_customer_ids_by_user_id_interface(self.current_user.id)
        if not customer_ids:
            return self.send_fail(error_text="订单不存在")
        ret, info = get_customer_order_with_detail_by_id(customer_ids, args.get("order_id"))
        if not ret:
            return self.send_fail(error_text=info)
        # 不需要顾客信息
        info.customer = None
        serializer = MallOrderSerializer(info)
        return self.send_success(data=serializer.data)


class MallCartVerifyView(MallBaseView):
    """商城端-购物篮确认时检验"""

    @use_args(
        {
            "product_ids": fields.List(
                fields.Integer(required=True),
                required=True,
                validate=[validate.Length(1)],
                comment="商品ID",
            )
        },
        location="json"
    )
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        product_list = list_product_by_ids_interface(shop.id, **args)
        for product in product_list:
            if product.status == ProductStatus.OFF:
                return self.send_fail(
                    error_text="商品{product_name}已下架, 看看别的商品吧".format(product_name=product.name)
                )
        return self.send_success()


class MallProductVerifyView(MallBaseView):
    """商城-确认订单时校验"""

    @use_args(
        {
            "product_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="货品ID"
            ),
        },
        location="json",
    )
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        product_id = args.get("product_id")
        # 验证下架
        product = get_product_by_id_interface(
            self.current_shop.id, product_id
        )
        if not product or product.status != ProductStatus.ON:
            return self.send_fail(error_text="商品已下架, 看看别的商品吧")
        return self.send_success()