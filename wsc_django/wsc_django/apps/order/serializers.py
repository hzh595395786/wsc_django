from django.db import transaction
from rest_framework import serializers

from customer.serializers import AdminCustomerSerializer
from customer.services import get_customer_by_user_id_and_shop_id, create_customer
from delivery.serializers import AdminDeliverySerializer
from order.services import create_order, _create_order_details, _create_order_address
from user.serializers import UserSerializer
from wsc_django.utils.constant import DateFormat
from wsc_django.utils.core import NumGenerator, FuncField
from wsc_django.utils.validators import delivery_method_validator, order_pay_type_validator


class OrderAddressSerializer(serializers.Serializer):
    """订单地址序列化器类"""

    name = serializers.CharField(label="收货人姓名")
    phone = serializers.CharField(label="收货人手机号")
    sex = serializers.IntegerField(label="收货人性别")
    address = serializers.CharField(label="详细地址")
    province = serializers.IntegerField(label="省编码")
    city = serializers.IntegerField(label="市编码")
    county = serializers.IntegerField(label="区编码")


class AdminOrderDetailSerializer(serializers.Serializer):
    """后台订单详情序列化器类"""

    product_id = serializers.IntegerField(label="商品id")
    product_name = serializers.CharField(label="商品名")
    product_cover_picture = serializers.CharField(label="商品封面图")
    quantity_net = FuncField(lambda value: round(float(value), 2), label="购买量")
    price_net = FuncField(lambda value: round(float(value), 2), label="单价")
    amount_net = FuncField(lambda value: round(float(value), 2), label="总价")


class AdminOrderSerializer(serializers.Serializer):
    """后台订单序列化器类"""

    id = serializers.IntegerField(label="订单id")
    delivery_method = serializers.IntegerField(
        required=True, validators=[delivery_method_validator], label="配送方式：1：送货上门，2：客户自提"
    )
    delivery_period = serializers.CharField(required=True, label="自提时间段（仅自提必传），举例：今天 12:00~13:00")
    order_num = serializers.CharField(required=True, label="订单号")
    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="下单时间")
    pay_type = serializers.IntegerField(
        required=True, validators=[order_pay_type_validator], label="支付方式：1：微信支付，2：货到付款"
    )
    amount_gross = serializers.DecimalField(
        write_only=True, required=True, max_digits=13, decimal_places=4, label="货款金额（优惠前）"
    )
    amount_net = serializers.DecimalField(required=True, max_digits=13, decimal_places=4, label="货款金额（优惠后）")
    delivery_amount_gross = serializers.DecimalField(
        write_only=True, required=True, max_digits=13, decimal_places=4, label="货款金额运费（优惠前）",
    )
    delivery_amount_net = serializers.DecimalField(
        required=True, max_digits=13, decimal_places=4, label="货款金额运费（优惠后）"
    )
    total_amount_gross = serializers.DecimalField(
        write_only=True, required=True, max_digits=13, decimal_places=4, label="订单金额（优惠前）"
    )
    total_amount_net = serializers.DecimalField(
        required=True, max_digits=13, decimal_places=4, label="订单金额（优惠后）"
    )
    remark = serializers.CharField(required=False, default="", min_length=0, max_length=30, label="订单备注")
    order_type = serializers.IntegerField(
        required=True, label="订单类型,1:普通订单，2：拼团订单"
    )
    address = OrderAddressSerializer(required=False, label="订单地址")
    order_status = serializers.IntegerField(required=False, label="订单状态")
    refund_type = serializers.IntegerField(required=False, label="退款方式")
    customer = AdminCustomerSerializer(required=False, label="订单对应的客户对象")
    delivery = AdminDeliverySerializer(required=False, label="订单对应的配送记录对象")
    order_details = AdminOrderDetailSerializer(required=False, many=True, label="订单对应的订单详情对象")


class AdminOrdersSerializer(serializers.Serializer):
    """后台订单列表序列化器类，不需要那么多信息"""

    id = serializers.IntegerField(label="订单id")
    delivery_method = serializers.IntegerField(
        required=True, validators=[delivery_method_validator], label="配送方式：1：送货上门，2：客户自提"
    )
    delivery_period = serializers.CharField(required=True, label="自提时间段（仅自提必传），举例：今天 12:00~13:00")
    order_num = serializers.CharField(required=True, label="订单号")
    order_status = serializers.IntegerField(required=False, label="订单状态")
    remark = serializers.CharField(required=False, default="", min_length=0, max_length=30, label="订单备注")
    pay_type = serializers.IntegerField(
        required=True, validators=[order_pay_type_validator], label="支付方式：1：微信支付，2：货到付款"
    )
    order_type = serializers.IntegerField(
        required=True, label="订单类型,1:普通订单，2：拼团订单"
    )
    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="下单时间")
    total_amount_net = serializers.DecimalField(
        required=True, max_digits=13, decimal_places=4, label="订单金额（优惠后）"
    )
    customer = AdminCustomerSerializer(required=False, label="订单对应的客户对象")
    order_details = AdminOrderDetailSerializer(required=False, many=True, label="订单对应的订单详情对象")


class MallOrderCreateSerializer(serializers.Serializer):
    """商城端订单创建序列化器类"""

    order_info = AdminOrderSerializer(label="订单内容")

    def create(self, validated_data):
        user = self.context["self"].current_user
        shop = self.context["self"].current_shop
        order_info = validated_data.get("order_info")
        address_info = order_info.pop("address")
        cart_items = self.context["cart_items"]
        with transaction.atomic():
            # 创建一个保存点
            save_id = transaction.savepoint()
            try:
                # 检查并创建客户
                customer = get_customer_by_user_id_and_shop_id(user.id, shop.id)
                if not customer:
                    customer = create_customer(user.id, shop.id)
                # 创建订单
                order = create_order(shop, customer, order_info)
                order.set_num(NumGenerator.generate(shop.id, order.order_type))
                # 创建订单详情
                success, storage_records = _create_order_details(order, cart_items, customer)
                if not success:
                    raise serializers.ValidationError(storage_records)
                for storage_record in storage_records:
                    storage_record.order_num = order.order_num
                    storage_record.save()
                # 创建订单地址
                address_info["order_id"] = order.id
                _create_order_address(address_info, shop.id, order_info["delivery_method"])
            except Exception as e:
                print(e)
                # 回滚到保存点
                transaction.savepoint_rollback(save_id)
                raise e
            # 提交事务
            transaction.savepoint_commit(save_id)
        return order


class MallOrderSerializer(AdminOrderSerializer):
    """商城端订单序列化器类"""

    amount_net = FuncField(lambda value: round(float(value), 2), label="货品总额")
    delivery_amount_net = FuncField(lambda value: round(float(value), 2), label="配送费/服务费")
    total_amount_net = FuncField(lambda value: round(float(value), 2), label="订单总额")


class MallOrdersSerializer(serializers.Serializer):
    """商城端订单列表序列化器类"""

    id = serializers.IntegerField(label="订单id")
    create_time = serializers.DateTimeField(format=DateFormat.TIME, label="下单时间")
    order_type = serializers.IntegerField(label="订单类型,1:普通订单，2：拼团订单")
    order_status = serializers.IntegerField(required=False, label="订单状态")
    delivery_method = serializers.IntegerField(label="配送方式：1：送货上门，2：客户自提")
    delivery_type = serializers.IntegerField(required=False, label="订单配送类型:员工/快递")
    total_amount_gross = serializers.DecimalField(max_digits=13, decimal_places=4, label="订单金额（优惠前）")
    order_details = AdminOrderDetailSerializer(required=False, many=True, label="订单对应的订单详情对象")


class OrderLogSerializer(serializers.Serializer):
    """订单日志序列化器类"""

    operate_type_text = serializers.CharField(label="操作类型文字版")
    operate_type = serializers.IntegerField(label="操作类型")
    operate_content = serializers.CharField(label="操作内容")
    operate_time = serializers.DateTimeField(format=DateFormat.TIME, label="操作时间")
    operator = UserSerializer(label="操作人信息")