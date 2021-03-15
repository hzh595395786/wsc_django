from rest_framework import status
from webargs.djangoparser import use_args
from webargs import fields, validate

from customer.constant import MineAddressDefault
from user.constant import Sex
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView, MallBaseView
from customer.serializers import (
    AdminCustomerSerializer,
    AdminCustomerPointsSerializer,
    MallMineAddressSerializer,
)
from customer.services import (
    update_customer_remark,
    get_mine_address_by_id,
    list_customer_by_shop_id,
    delete_mine_address_by_id,
    list_customer_point_by_customer_id,
    get_customer_by_customer_id_and_shop_id,
    list_mine_address_by_user_id_and_shop_id,
    get_mine_default_address_by_user_id_and_shop_id,
)



class AdminCustomerView(AdminBaseView):
    """后台-客户-客户详情"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CUSTOMER]
    )
    @use_args({"customer_id": fields.Integer(required=True, comment="客户ID")}, location="query")
    def get(self, request, args):
        customer_id = args.get("customer_id")
        customer = get_customer_by_customer_id_and_shop_id(
            customer_id,
            self.current_shop.id,
            with_user_info=True
        )
        if customer:
            serializer = AdminCustomerSerializer(customer)
            return self.send_success(data=serializer.data)
        else:
            return self.send_fail(error_text="客户不存在")


class AdminCustomersView(AdminBaseView):
    """后台-客户-客户列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CUSTOMER]
    )
    @use_args(
        {
            "sort_prop": fields.String(
                required=False,
                missing="",
                validate=[validate.OneOf(["", "consume_amount", "consume_count"])],
                comment="排序字段",
            ),
            "sort": fields.Function(
                deserialize=lambda x: x.rstrip("ending"),
                required=False,
                missing="",
                validate=[validate.OneOf(["", "asc", "desc"])],
                comment="排序方式, +:正序，-:倒序",
            ),
            "keyword": fields.String(
                required=False, missing="", comment="搜索关键字,昵称或者手机号"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        shop = self.current_shop
        customer_list = list_customer_by_shop_id(shop.id, **args)
        customer_list = self._get_paginated_data(customer_list, AdminCustomerSerializer)
        return self.send_success(data_list=customer_list)


class AdminCustomerRemarkView(AdminBaseView):
    """后台-客户-更改客户备注"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CUSTOMER]
    )
    @use_args(
        {
            "customer_id": fields.Integer(required=True, comment="客户ID"),
            "remark": fields.String(required=True, validate=[validate.Length(0, 20)]),
        },
        location="json",
    )
    def put(self, request, args):
        shop = self.current_shop
        customer = get_customer_by_customer_id_and_shop_id(args.get("customer_id"), shop.id)
        if not customer:
            return self.send_fail(error_text="客户或customer_id不存在")
        update_customer_remark(customer, args.get("remark"))
        return self.send_success()


class AdminCustomerPointsView(AdminBaseView):
    """后台-客户-历史积分查询"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CUSTOMER]
    )
    @use_args(
        {
            "customer_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="客户ID"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        shop = self.current_shop
        customer_id = args.get("customer_id")
        customer = get_customer_by_customer_id_and_shop_id(customer_id, shop.id)
        if not customer:
            return self.send_fail(error_text="客户不存在")
        customer_point_list = list_customer_point_by_customer_id(customer.id)
        customer_point_list = self._get_paginated_data(customer_point_list, AdminCustomerPointsSerializer)
        return self.send_success(data_list=customer_point_list)


class MallMineAddressView(MallBaseView):
    """商城-我的-添加收货地址&获取收货地址列表&编辑收货地址&删除地址"""
    pagination_class = StandardResultsSetPagination

    def get(self, request, shop_code):
        self._set_current_shop(request, shop_code)
        user = self.current_user
        shop = self.current_shop
        mine_address_list = list_mine_address_by_user_id_and_shop_id(user.id, shop.id)
        mine_address_list = self._get_paginated_data(mine_address_list, MallMineAddressSerializer)
        return self.send_success(data_list=mine_address_list)

    @use_args(
        {
            "name": fields.String(
                required=True,
                validate=[validate.Length(1)],
                comment="收货人姓名",
            ),
            "sex": fields.Integer(
                required=False,
                default=Sex.UNKNOWN,
                validate=[validate.OneOf([Sex.UNKNOWN, Sex.MALE, Sex.FEMALE])],
                comment="性别",
            ),
            "phone": fields.String(required=True, comment="手机号"),
            "province": fields.Integer(
                required=True, comment="省份编码"
            ),
            "city": fields.Integer(required=True, comment="城市编码"),
            "county": fields.Integer(
                required=True, comment="区份编码"
            ),
            "address": fields.String(
                required=True,
                validate=[validate.Length(1, 50)],
                comment="详细地址",
            ),
            "default": fields.Integer(
                required=False,
                default=MineAddressDefault.NO,
                validate=[validate.OneOf([MineAddressDefault.YES, MineAddressDefault.NO])],
                comment="是否为默认地址",
            ),
            "longitude": fields.Float(
                required=False,
                validate=[validate.Range(-180, 180)],
                comment="经度",
            ),
            "latitude": fields.Float(
                required=False,
                validate=[validate.Range(-90, 90)],
                comment="纬度",
            ),
        },
        location="json",
    )
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        serializer = MallMineAddressSerializer(data=args, context={"self": self})
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success(data=serializer.data)

    @use_args(
        {
            "address_id": fields.Integer(
                required=True,
                validate=[validate.Range(1)],
                comment="地址ID",
            ),
            "name": fields.String(required=True, comment="收货人姓名"),
            "sex": fields.Integer(
                required=False,
                default=Sex.UNKNOWN,
                validate=[validate.OneOf([Sex.UNKNOWN, Sex.MALE, Sex.FEMALE])],
                comment="性别",
            ),
            "phone": fields.String(required=True, comment="手机号"),
            "province": fields.Integer(
                required=True, comment="省份编码"
            ),
            "city": fields.Integer(required=True, comment="城市编码"),
            "county": fields.Integer(
                required=True, comment="区份编码"
            ),
            "address": fields.String(
                required=True,
                validate=[validate.Length(1, 50)],
                comment="详细地址",
            ),
            "default": fields.Integer(
                required=False,
                default=MineAddressDefault.NO,
                validate=[validate.OneOf([MineAddressDefault.NO, MineAddressDefault.YES])],
                comment="是否为默认地址",
            ),
            "longitude": fields.Float(
                required=False,
                validate=[validate.Range(-180, 180)],
                comment="经度",
            ),
            "latitude": fields.Float(
                required=False,
                validate=[validate.Range(-90, 90)],
                comment="纬度",
            ),
        },
        location="json",
    )
    def put(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        address_id = args.pop("address_id")
        user = self.current_user
        shop = self.current_shop
        mine_address = get_mine_address_by_id(address_id, user.id, shop.id)
        if not mine_address:
            return self.send_fail(error_text="地址不存在")
        serializer = MallMineAddressSerializer(mine_address, data=args)
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success()

    @use_args(
        {
            "address_id": fields.Integer(
                required=True,
                validate=[validate.Range(1)],
                comment="地址ID",
            )
        },
        location="json",
    )
    def delete(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        user = self.current_user
        shop = self.current_shop
        address_id = args.get("address_id")
        ret, info = delete_mine_address_by_id(address_id, user.id, shop.id)
        if not ret:
            return self.send_fail(error_text=info)
        else:
            return self.send_success()


class MallMineDefaultAddressView(MallBaseView):
    """商城-获取一个用户的默认地址"""

    def get(self, request, shop_code):
        self._set_current_shop(request, shop_code)
        user = self.current_user
        shop = self.current_shop
        default_address = get_mine_default_address_by_user_id_and_shop_id(user.id, shop.id)
        if not default_address:
            return self.send_fail(error_text="还未设置默认地址")
        serializer = MallMineAddressSerializer(default_address)
        return self.send_success(data=serializer.data)