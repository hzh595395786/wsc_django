import decimal

from rest_framework import status
from webargs import fields, validate
from webargs.djangoparser import use_args

from delivery.constant import DeliveryType
from delivery.serializers import AdminDeliverySerializer
from logs.constant import OrderLogType
from order.constant import OrderDeliveryMethod, OrderPayType, OrderType, OrderStatus, OrderRefundType
from order.services import order_data_check, set_order_paid, cancel_order, count_paid_order, \
    set_order_status_confirmed_finish, refund_order
from wsc_django.utils.arguments import StrToList
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import MallBaseView, AdminBaseView
from product.constant import ProductStatus
from user.constant import Sex
from order.selectors import (
    get_customer_order_with_detail_by_id,
    get_customer_order_by_id,
    list_customer_order_by_customer_ids,
    list_shop_orders, count_abnormal_order, get_shop_order_by_num,
    get_shop_order_by_num_without_details,
    get_shop_order_by_shop_id_and_id,
    get_order_by_shop_id_and_id, list_shop_abnormal_orders)
from order.serializers import (
    MallOrderCreateSerializer,
    MallOrderSerializer,
    MallOrdersSerializer,
    AdminOrdersSerializer,
    AdminOrderSerializer,
    OrderLogSerializer
)
from order.interface import (
    list_product_by_ids_interface,
    get_product_by_id_interface,
    jsapi_params_interface,
    auto_cancel_order_interface,
    order_commit_tplmsg_interface,
    list_customer_ids_by_user_id_interface,
    get_customer_by_user_id_and_shop_id_interface,
    list_order_log_by_shop_id_and_order_num_interface,
    get_order_delivery_by_delivery_id_interface,
    print_order_interface, create_order_delivery_interface, get_msg_notify_by_shop_id_interface,
    order_delivery_tplmsg_interface, order_finish_tplmsg_interface, order_refund_tplmsg_interface)


class AdminOrdersView(AdminBaseView):
    """后台-订单-获取订单列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_types": StrToList(
                required=False,
                missing=[OrderType.NORMAL, OrderType.GROUPON],
                validate=[validate.ContainsOnly([OrderType.NORMAL, OrderType.GROUPON])],
                comment="订单类型筛选 1: 普通订单, 5: 拼团订单",
            ),
            "order_pay_types": StrToList(
                required=False,
                missing=[OrderPayType.WEIXIN_JSAPI, OrderPayType.ON_DELIVERY],
                validate=[
                    validate.ContainsOnly(
                        [OrderPayType.WEIXIN_JSAPI, OrderPayType.ON_DELIVERY]
                    )
                ],
                comment="订单支付方式筛选 1: 微信支付, 2: 货到付款",
            ),
            "order_delivery_methods": StrToList(
                required=False,
                missing=[
                    OrderDeliveryMethod.HOME_DELIVERY,
                    OrderDeliveryMethod.CUSTOMER_PICK,
                ],
                validate=[
                    validate.ContainsOnly(
                        [
                            OrderDeliveryMethod.HOME_DELIVERY,
                            OrderDeliveryMethod.CUSTOMER_PICK,
                        ]
                    )
                ],
                comment="订单配送方式筛选 1: 送货上门, 2: 自提",
            ),
            "order_status": StrToList(
                required=False,
                missing=[
                    OrderStatus.PAID,
                    OrderStatus.CONFIRMED,
                    OrderStatus.FINISHED,
                    OrderStatus.REFUNDED,
                ],
                validate=[
                    validate.ContainsOnly(
                        [
                            OrderStatus.PAID,
                            OrderStatus.CONFIRMED,
                            OrderStatus.FINISHED,
                            OrderStatus.REFUNDED,
                        ]
                    )
                ],
                comment="订单状态筛选 2: 未处理 3: 处理中 4: 已完成 5: 已退款",
            ),
            "num": fields.String(
                required=False, data_key="order_num", comment="订单号搜索，与其他条件互斥"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        shop_id = self.current_shop.id
        order_list = list_shop_orders(shop_id, **args)
        order_list = self._get_paginated_data(order_list, AdminOrdersSerializer)
        return self.send_success(data_list=order_list)


class AdminOrderView(AdminBaseView):
    """后台-订单-获取订单详情"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_num": fields.String(
                comment="订单id", validate=lambda num: len(num) == 19
            )
        },
        location="query"
    )
    def get(self, request, args):
        success, order = get_shop_order_by_num(
            self.current_shop.id, args["order_num"]
        )
        if not success:
            return self.send_fail(error_text=order)
        serializer = AdminOrderSerializer(order)
        return self.send_success(data=serializer.data)


class AdminOrderPrintView(AdminBaseView):
    """后台-订单-打印订单"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args({"order_id": fields.Integer(required=True, comment="打印的订单id")}, location="json")
    def post(self, request, args):
        success, order = get_shop_order_by_shop_id_and_id(
            self.current_shop.id, args["order_id"]
        )
        if not success:
            return self.send_fail(error_text=order)
        success, msg = print_order_interface(order, self.current_user.id)
        if not success:
            return self.send_fail(error_text=msg)
        return self.send_success()


class AdminOrderConfirmView(AdminBaseView):
    """后台-订单-开始订单"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            ),
            "delivery_type": fields.Integer(
                required=False,
                validate=[
                    validate.OneOf(
                        [DeliveryType.ExpressDelivery, DeliveryType.StaffDelivery]
                    )
                ],
                comment="配送类型",
            ),
            "express": fields.Nested(
                {
                    "company": fields.String(required=True, comment="快递公司"),
                    "express_num": fields.String(required=True, comment="快递单号"),
                },
                required=False,
                unknown=True,
                comment="快递信息",
            ),
        },
        location="json",
    )
    def post(self, request, args):
        shop_id = self.current_shop.id
        order = get_order_by_shop_id_and_id(shop_id, args.get("order_id"))
        if not order:
            return self.send_fail(error_text="订单不存在")
        elif order.order_status != OrderStatus.PAID:
            return self.send_fail(error_text="订单状态已改变")
        # 送货上门
        if order.delivery_method == OrderDeliveryMethod.HOME_DELIVERY:
            if not args.get("delivery_type"):
                return self.send_fail(error_text="送货上门必须选择配送方式")
            if args.get(
                "delivery_type"
            ) == DeliveryType.ExpressDelivery and not args.get("express"):
                return self.send_fail(error_text="快递配送必须填写快递公司与单号")
            # 创建一个配送记录
            delivery_info = {"delivery_type": args.get("delivery_type")}
            delivery_info.update(args.get("express", {}))
            delivery = create_order_delivery_interface(delivery_info)
            order.delivery_id = delivery.id

        set_order_status_confirmed_finish(
            order,
            OrderStatus.CONFIRMED,
            self.current_user.id,
            OrderLogType.CONFIRM,
        )
        # 获取店铺的消息提醒设置, 发送订单配送通知(订单确认)
        msg_notify = get_msg_notify_by_shop_id_interface(shop_id)
        # if msg_notify.order_confirm_wx:
        #     order_delivery_tplmsg_interface(order.id)
        return self.send_success()


class AdminOrderDirectView(AdminBaseView):
    """后台-订单-一键完成订单"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            )
        },
        location="json",
    )
    def post(self, request, args):
        shop_id = self.current_shop.id
        order = get_order_by_shop_id_and_id(shop_id, args.get("order_id"))
        if not order:
            return self.send_fail(error_text="订单不存在")
        elif order.order_status != OrderStatus.PAID:
            return self.send_fail(error_text="订单状态已改变")
        # 创建一个配送记录
        if order.delivery_method == OrderDeliveryMethod.HOME_DELIVERY:
            delivery_info = {"delivery_type": DeliveryType.StaffDelivery}
            delivery = create_order_delivery_interface(delivery_info)
            order.delivery_id = delivery.id
        set_order_status_confirmed_finish(
            order,
            OrderStatus.FINISHED,
            self.current_user.id,
            OrderLogType.DIRECT,
        )
        msg_notify = get_msg_notify_by_shop_id_interface(shop_id)
        # if msg_notify.order_finish_wx:
        #     order_finish_tplmsg_interface(order.id)
        return self.send_success()


class AdminOrderFinishView(AdminBaseView):
    """后台-订单-完成订单"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            )
        },
        location="json",
    )
    def post(self, request, args):
        shop_id = self.current_shop.id
        order = get_order_by_shop_id_and_id(shop_id, args.get("order_id"))
        if not order:
            return self.send_fail(error_text="订单不存在")
        elif order.order_status != OrderStatus.CONFIRMED:
            return self.send_fail(error_text="订单状态已改变")
        set_order_status_confirmed_finish(
            order,
            OrderStatus.FINISHED,
            self.current_user.id,
            OrderLogType.FINISH,
        )
        # 获取店铺的消息提醒设置, 发送微信模板消息
        msg_notify = get_msg_notify_by_shop_id_interface(shop_id)
        if msg_notify.order_finish_wx:
            order_finish_tplmsg_interface(order.id)
        return self.send_success()


class AdminOrderRefundView(AdminBaseView):
    """后台-订单-退款"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            ),
            "refund_type": fields.Integer(
                required=True,
                validate=[
                    validate.OneOf(
                        [
                            OrderRefundType.WEIXIN_JSAPI_REFUND,
                            OrderRefundType.UNDERLINE_REFUND,
                        ]
                    )
                ],
            ),
        },
        location="json",
    )
    def post(self, request, args):
        shop_id = self.current_shop.id
        order = get_order_by_shop_id_and_id(shop_id, args.get("order_id"))
        if not order:
            return self.send_fail(error_text="订单不存在")
        elif order.status not in [
            OrderStatus.PAID,
            OrderStatus.CONFIRMED,
            OrderStatus.FINISHED,
            OrderStatus.REFUND_FAIL,
        ]:
            return self.send_fail(error_text="订单状态已改变")
        if (
            order.pay_type == OrderPayType.ON_DELIVERY
            and args["refund_type"] == OrderRefundType.WEIXIN_JSAPI_REFUND
        ):
            return self.send_fail(error_text="货到付款的订单只能进行线下退款")
        success, msg = refund_order(
            self.current_shop.id,
            order,
            args["refund_type"],
            self.current_user.id,
        )
        if not success:
            return self.send_fail(error_obj=msg)
        # 获取店铺的消息提醒设置, 发送微信模板消息
        msg_notify = get_msg_notify_by_shop_id_interface(shop_id)
        # if msg_notify.order_refund_wx and order.pay_type == OrderPayType.WEIXIN_JSAPI:
        #     order_refund_tplmsg_interface(order.id)
        return self.send_success()


class AdminOrderOperateLogView(AdminBaseView):
    """后台-订单-订单操作记录"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_num": fields.String(
                comment="订单id", validate=lambda num: len(num) == 19
            )
        },
        location="query"
    )
    def get(self, request, args):
        shop_id = self.current_shop.id
        order = get_shop_order_by_num_without_details(shop_id, args["order_num"])
        if not order:
            return self.send_fail(error_text="订单不存在")
        # 操作记录获取
        log_list = list_order_log_by_shop_id_and_order_num_interface(shop_id, order.order_num)
        # 配送信息获取
        delivery = get_order_delivery_by_delivery_id_interface(order.delivery_id)
        delivery_data = AdminDeliverySerializer(delivery).data
        # 打印次数获取
        print_count = 0
        for ll in log_list:
            if ll.operate_type == OrderLogType.PRINT:
                print_count += 1
        # 分页操作
        log_list = self._get_paginated_data(log_list, OrderLogSerializer)
        data = {
            "log_list": log_list,
            "delivery": delivery_data,
            "print_count": print_count,
        }
        return self.send_success(data=data)


class AdminOrderPaidCountView(AdminBaseView):
    """后台-订单-未处理订单数"""

    def get(self, request):
        count = count_paid_order(self.current_shop.id)
        return self.send_success(count=count)


class AdminAbnormalOrderCountView(AdminBaseView):
    """后台-订单-异常订单数"""

    def get(self, request):
        count = count_abnormal_order(self.current_shop.id)
        return self.send_success(count=count)


class AdminAbnormalOrdersView(AdminBaseView):
    """后台-订单-获取异常订单列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_ORDER]
    )
    @use_args(
        {
            "order_types": StrToList(
                required=False,
                missing=[OrderType.GROUPON],
                validate=[validate.ContainsOnly([OrderType.GROUPON])],
                comment="订单类型筛选 1: 普通订单, 5: 拼团订单",
            ),
            "order_pay_types": StrToList(
                required=False,
                missing=[OrderPayType.ON_DELIVERY, OrderPayType.WEIXIN_JSAPI],
                validate=[
                    validate.ContainsOnly(
                        [OrderPayType.WEIXIN_JSAPI, OrderPayType.ON_DELIVERY]
                    )
                ],
                comment="订单支付方式筛选 1: 微信支付, 2: 货到付款",
            ),
            "order_delivery_methods": StrToList(
                required=False,
                missing=[DeliveryType.StaffDelivery, DeliveryType.ExpressDelivery],
                validate=[
                    validate.ContainsOnly(
                        [DeliveryType.ExpressDelivery, DeliveryType.StaffDelivery]
                    )
                ],
                comment="订单配送方式筛选 1: 送货上门, 2: 自提",
            ),
            "order_status": StrToList(
                required=False,
                missing=[OrderStatus.REFUND_FAIL],
                validate=[validate.ContainsOnly([OrderStatus.REFUND_FAIL])],
                comment="订单状态筛选 6: 退款失败",
            ),
            "order_num": fields.String(comment="订单号搜索，与其他条件互斥"),
        },
        location="query"
    )
    def get(self, request, args):
        orders = list_shop_abnormal_orders(
            self.current_shop.id, **args
        )
        orders = self._get_paginated_data(orders, AdminOrderSerializer)
        return self.send_success(data_list=orders)


class MallOrderView(MallBaseView):
    """商城端-提交订单&订单详情"""

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


class MallOrdersView(MallBaseView):
    """商城-订单列表"""
    pagination_class = StandardResultsSetPagination

    def get(self, reuqest, shop_code):
        self._set_current_shop(reuqest, shop_code)
        user_id = self.current_user.id
        shop_id = self.current_shop.id
        customer = get_customer_by_user_id_and_shop_id_interface(user_id, shop_id)
        # 不是客户在这个店肯定没单
        if not customer:
            return self.send_success(data_list=[])
        order_list = list_customer_order_by_customer_ids([customer.id])
        order_list = self._get_paginated_data(order_list, MallOrdersSerializer)
        return self.send_success(data_list=order_list)


class MallOrderCancellationView(MallBaseView):
    """商城-订单-取消订单"""

    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            )
        },
        location="json",
    )
    def put(self, request, args):
        customer_ids = list_customer_ids_by_user_id_interface(self.current_user.id)
        if not customer_ids:
            return self.send_fail(error_text="订单不存在")
        order = get_customer_order_by_id(customer_ids, args.get("order_id"))
        if not order:
            return self.send_fail(error_text="订单不存在")
        if order.order_status != OrderStatus.UNPAID:
            return self.send_fail(error_text="订单状态已改变")
        success, msg = cancel_order(order.shop_id, order.id)
        if not success:
            return self.send_fail(error_obj=msg)
        return self.send_success()


class MallOrderPaymentView(MallBaseView):
    """商城-订单-支付"""

    @use_args(
        {
            "order_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="订单ID"
            ),
            "wx_openid": fields.String(required=True, comment="微信openID"),
        },
        location="json",
    )
    def put(self, request, args):
        customer_ids = list_customer_ids_by_user_id_interface(self.current_user.id)
        if not customer_ids:
            return self.send_fail(error_text="订单不存在")
        order = get_customer_order_by_id(customer_ids, args.get("order_id"))
        assert order.pay_type == OrderPayType.WEIXIN_JSAPI

        if not order:
            return self.send_fail(error_text="订单不存在")
        elif order.order_status != OrderStatus.UNPAID:
            return self.send_fail(error_text="订单状态已改变")
        success, params = jsapi_params_interface(order, args["wx_openid"])
        if not success:
            return self.send_fail(error_obj=params)
        return self.send_success(data=params)
