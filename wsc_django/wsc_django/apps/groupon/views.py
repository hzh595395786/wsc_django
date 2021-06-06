from rest_framework import status
from webargs import fields, validate
from webargs.djangoparser import use_args

from groupon.constant import GrouponType, GrouponStatus, GrouponAttendStatus
from order.serializers import AdminOrdersSerializer
from product.services import get_product_by_id
from wsc_django.utils.arguments import StrToList
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView, MallBaseView
from groupon.interface import (
    expire_groupon_interface,
    publish_gruopon_interface,
    immediate_cancel_order_interface,
    sync_success_groupon_attend_interface,
    immediate_fail_groupon_attend_interface,
    list_order_by_groupon_attend_id_interface,
    list_unpay_order_by_groupon_attend_ids_interface,
    delay_fail_groupon_attend_interface)
from groupon.serializers import (
    AdminGrouponSerializer,
    AdminGrouponsSerializer,
    AdminGrouponCreateSerializer,
    AdminGrouponAttendSerializer,
)
from groupon.services import (
    set_groupon_off,
    list_shop_groupons,
    launch_groupon_attend,
    get_shop_groupon_by_id,
    validate_groupon_period,
    force_success_groupon_attend,
    list_waitting_groupon_attends,
    get_shop_groupon_attend_by_id,
    list_groupon_attends_by_groupon,
    list_created_groupon_attends_by_groupon_id,
)



class AdminGrouponView(AdminBaseView):
    """后台-玩法-拼团-创建拼团&编辑拼团&拼团活动详情获取"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "product_id": fields.Integer(required=True, comment="商品id"),
            "price": fields.Decimal(required=True, comment="拼团价"),
            "from_datetime": fields.DateTime(required=True, comment="拼团活动开始时间"),
            "to_datetime": fields.DateTime(required=True, comment="拼团活动结束时间"),
            "groupon_type": fields.Integer(
                required=True,
                validate=[validate.OneOf([GrouponType.NORMAL, GrouponType.MENTOR])],
                comment="拼团活动类型 1:普通 2:老带新",
            ),
            "success_size": fields.Integer(
                required=True, validate=[validate.Range(2, 50)], comment="成团人数"
            ),
            "quantity_limit": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="购买数量上限"
            ),
            "success_limit": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="成团数量上限"
            ),
            "attend_limit": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="参团数量上限"
            ),
            "success_valid_hour": fields.Integer(
                required=True, validate=[validate.OneOf([24, 48])], comment="开团有效时间"
            ),
        },
        location="json"
    )
    def post(self, request, args):
        success, msg = validate_groupon_period(
            args["product_id"], args["from_datetime"], args["to_datetime"]
        )
        if not success:
            return self.send_fail(error_text=msg)
        product = get_product_by_id(self.current_shop.id, args.pop("product_id"), filter_delete=False)
        if not product:
            return self.send_fail(error_text="货品不存在")
        serializer = AdminGrouponCreateSerializer(
            data=args, context={"self": self, "product": product}
        )
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        groupon = serializer.save()
        publish_gruopon_interface(groupon)
        expire_groupon_interface(groupon)
        return self.send_success()

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args({"groupon_id": fields.String(required=True, comment="拼团id")}, location="query")
    def get(self, request, args):
        success, groupon = get_shop_groupon_by_id(
            self.current_shop.id, args["groupon_id"]
        )
        if not success:
            return self.send_fail(error_text=groupon)
        serializer = AdminGrouponSerializer(groupon)
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "groupon_id": fields.Integer(required=True, comment="拼团id"),
            "product_id": fields.Integer(required=True, comment="商品id"),
            "price": fields.Decimal(required=True, comment="拼团价"),
            "from_datetime": fields.DateTime(required=True, comment="拼团活动开始时间"),
            "to_datetime": fields.DateTime(required=True, comment="拼团活动结束时间"),
            "groupon_type": fields.Integer(
                required=True,
                validate=[validate.OneOf([GrouponType.NORMAL, GrouponType.MENTOR])],
                comment="拼团活动类型 1:普通 2:老带新",
            ),
            "success_size": fields.Integer(
                required=True, validate=[validate.Range(2, 50)], comment="成团人数"
            ),
            "quantity_limit": fields.Integer(required=True, comment="购买数量上限"),
            "success_limit": fields.Integer(required=True, comment="成团数量上限"),
            "attend_limit": fields.Integer(required=True, comment="参团数量上限"),
            "success_valid_hour": fields.Integer(
                required=True, validate=[validate.OneOf([24, 48])], comment="开团有效时间"
            ),
        },
        location="json"
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        product = get_product_by_id(
            shop_id, args.pop("product_id"), filter_delete=False
        )
        if not product:
            return self.send_fail(error_text="货品不存在")
        success, groupon = get_shop_groupon_by_id(shop_id, args.pop("groupon_id"))
        if not success:
            return self.send_fail(error_text=groupon)
        elif groupon.status == GrouponStatus.ON:
            return self.send_fail(error_text="拼团活动正在启用中，请停用后再进行编辑")
        success, msg = validate_groupon_period(
            product.id,
            args["from_datetime"],
            args["to_datetime"],
            groupon_id=groupon.id,
        )
        if not success:
            return self.send_fail(error_text=msg)
        states = [
            GrouponAttendStatus.CREATED,
            GrouponAttendStatus.WAITTING,
            GrouponAttendStatus.SUCCEEDED,
            GrouponAttendStatus.FAILED,
        ]
        groupon_attends = list_groupon_attends_by_groupon(groupon, states)
        if groupon_attends:
            return self.send_fail(error_text="已经有用户参团, 拼团无法编辑")
        serializer = AdminGrouponCreateSerializer(
            groupon, data=args, context={"self": self, "product": product}
        )
        # 参数已在use_args中验证，此处不在验证
        serializer.is_valid()
        groupon = serializer.save()
        publish_gruopon_interface(groupon)
        expire_groupon_interface(groupon)
        return self.send_success()


class AdminGrouponPeriodVerificationView(AdminBaseView):
    """后台-玩法-拼团-验证时间段"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "product_id": fields.Integer(required=True, comment="商品id"),
            "from_datetime": fields.DateTime(required=True, comment="拼团活动开始时间"),
            "to_datetime": fields.DateTime(required=True, comment="拼团活动结束时间"),
        },
        location="json"
    )
    def post(self, request, args):
        success, msg = validate_groupon_period(
            args["product_id"], args["from_datetime"], args["to_datetime"]
        )
        if not success:
            return self.send_fail(error_text=msg)
        return self.send_success()


class AdminGrouponOffView(AdminBaseView):
    """后台-玩法-拼团-停用拼团活动"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args({"groupon_id": fields.Integer(required=True, comment="拼团id")}, location="json")
    def post(self, request, args):
        success, groupon = set_groupon_off(
            self.current_shop.id, self.current_user.id, args["groupon_id"]
        )
        if not success:
            return self.send_fail(error_text=groupon)
        success, waitting_groupon_attends = list_waitting_groupon_attends(
            self.current_shop.id, groupon.id
        )
        if not success:
            raise ValueError("拼团{}停用成功，但是退款失败".format(groupon.id))
        for groupon_attend in waitting_groupon_attends:
            immediate_fail_groupon_attend_interface(
                self.current_shop.id, groupon_attend
            )
        # 拿到已创建的拼团参与(只有团长未支付才会处于这种状态）
        created_groupon_attends = list_created_groupon_attends_by_groupon_id(groupon.id)
        created_groupon_attend_ids = [
            groupon_attend.id for groupon_attend in created_groupon_attends
        ]
        waiting_pay_open_groupon_orders = list_unpay_order_by_groupon_attend_ids_interface(
            created_groupon_attend_ids
        )
        for order in waiting_pay_open_groupon_orders:
            immediate_cancel_order_interface(self.current_shop.id, order.id)
        return self.send_success()


class AdminGrouponsView(AdminBaseView):
    """后台-玩法-拼团-列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "product_name": fields.String(missing=None, comment="商品名搜索"),
        },
        location="query"
    )
    def get(self, request, args):
        groupons = list_shop_groupons(self.current_shop.id, args)
        groupons = self._get_paginated_data(groupons, AdminGrouponsSerializer)
        return self.send_success(data_list=groupons)


class AdminGrouponAttendsView(AdminBaseView):
    """后台-玩法-拼团-参与拼团列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "groupon_id": fields.Integer(required=True, comment="拼团id"),
            "groupon_attend_status": StrToList(
                required=False,
                missing=[
                    GrouponAttendStatus.WAITTING,
                    GrouponAttendStatus.SUCCEEDED,
                    GrouponAttendStatus.FAILED,
                ],
                validate=validate.ContainsOnly(
                    [
                        GrouponAttendStatus.WAITTING,
                        GrouponAttendStatus.SUCCEEDED,
                        GrouponAttendStatus.FAILED,
                    ]
                ),
                comment="拼团参与状态,1:拼团中 2:已成团 3:已失败",
            ),
        },
        location="query"
    )
    def get(self, request, args):
        success, groupon = get_shop_groupon_by_id(
            self.current_shop.id, args.pop("groupon_id")
        )
        if not success:
            return self.send_fail(error_text=groupon)
        groupon_attends = list_groupon_attends_by_groupon(groupon, args["groupon_attend_status"])
        groupon_attends = self._get_paginated_data(groupon_attends, AdminGrouponAttendSerializer)
        return self.send_success(data_list=groupon_attends)


class AdminGrouponAttendView(AdminBaseView):
    """后台-玩法-拼团-参与拼团详情"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args({"groupon_attend_id": fields.Integer(required=True, comment="拼团参与id")}, location="query")
    def get(self, request, args):
        success, groupon_attend = get_shop_groupon_attend_by_id(
            self.current_shop.id, args["groupon_attend_id"]
        )
        if not success:
            return self.send_fail(error_text=groupon_attend)
        serializer = AdminGrouponAttendSerializer(groupon_attend)
        return self.send_success(data=serializer.data)


class AdminGrouponAttendOrdersView(AdminBaseView):
    """后台-玩法-拼团-拼团参与详情-成员订单"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args(
        {
            "groupon_attend_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="拼团参与ID"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        args["shop_id"] = self.current_shop.id
        order_list = list_order_by_groupon_attend_id_interface(**args)
        order_list = self._get_paginated_data(order_list, AdminOrdersSerializer)
        return self.send_success(data_list=order_list)


class AdminGrouponAttendSuccessForceView(AdminBaseView):
    """后台-玩法-拼团-强制成功参与拼团"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PROMOTION]
    )
    @use_args({"groupon_attend_id": fields.Integer(required=True, comment="拼团参与id")}, location="query")
    def post(self, request, args):
        success, groupon_attend = force_success_groupon_attend(
            self.current_shop.id, args["groupon_attend_id"]
        )
        if not success:
            return self.send_fail(error_text=groupon_attend)
        sync_success_groupon_attend_interface(self.current_shop.id, groupon_attend.id)
        return self.send_success()


class MallGrouponAttendInitationView(MallBaseView):
    """商城-玩法-拼团-开团"""

    @use_args({"groupon_id": fields.Integer(required=True, comment="拼团活动id")}, location="json")
    def post(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        success, groupon_attend = launch_groupon_attend(
            self.current_shop.id, self.current_user.id, args["groupon_id"]
        )
        if not success:
            return self.send_fail(error_text=groupon_attend)
        delay_fail_groupon_attend_interface(self.current_shop.id, groupon_attend)
        return self.send_success(groupon_attend_id=groupon_attend.id)