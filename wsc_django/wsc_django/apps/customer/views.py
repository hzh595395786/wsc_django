from rest_framework import status
from webargs.djangoparser import use_args
from webargs import fields, validate

from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView
from customer.serializers import AdminCustomerSerializer, AdminCustomerPointsSerializer
from customer.services import (
    update_customer_remark,
    list_customer_by_shop_id,
    list_customer_point_by_customer_id,
    get_customer_by_customer_id_and_shop_id,
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