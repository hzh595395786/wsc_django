from webargs import fields, validate
from rest_framework import status
from webargs.djangoparser import use_args

from shop.constant import ShopStatus, ShopVerifyActive, ShopVerifyType
from shop.models import Shop
from staff.constant import StaffRole
from staff.serializers import StaffSerializer
from user.constant import USER_OUTPUT_CONSTANT
from user.serializers import UserSerializer
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import UserBaseView, AdminBaseView, MallBaseView
from shop.serializers import (
    ShopCreateSerializer,
    SuperShopSerializer,
    SuperShopListSerializer,
    SuperShopStatusSerializer,
    AdminShopSerializer,
    MallShopSerializer,
    SuperShopVerifySerializer,
)
from shop.services import (
    get_shop_by_shop_id,
    list_shop_by_shop_ids,
    list_shop_reject_reason,
    list_shop_by_shop_status,
    list_shop_creator_history_realname,
    get_shop_product_species_count_by_shop_ids,
)
from shop.interface import (
    list_staff_by_user_id_interface,
    get_user_by_id_interface,
    list_user_by_ids_interface,
    get_customer_by_user_id_and_shop_id_interface
)


class SuperShopView(UserBaseView):
    """总后台-商铺-商铺创建&商铺详情"""

    @use_args(
        {
            "user_id": fields.String(required=True, validate=validate.Range(1), comment="用户id"),
            "shop_data": fields.Nested(
                {
                    "shop_name": fields.String(
                        required=True, validate=[validate.Length(0, 128)], comment="店铺名"
                    ),
                    "shop_img": fields.String(
                        required=True,
                        validate=[validate.Length(0, 300)],
                        comment="店铺logo",
                    ),
                    "shop_province": fields.Integer(required=True, comment="省份编码"),
                    "shop_city": fields.Integer(required=True, comment="城市编码"),
                    "shop_county": fields.Integer(required=True, comment="区份编码"),
                    "shop_address": fields.String(
                        required=True,
                        validate=[validate.Length(0, 100)],
                        comment="详细地址",
                    ),
                    "description": fields.String(
                        required=True, validate=[validate.Length(0, 200)], comment="描述"
                    ),
                    "inviter_phone": fields.String(
                        required=True,
                        validate=[validate.Length(0, 32)],
                        comment="推荐人手机号",
                    ),
                    "longitude": fields.Decimal(
                        required=False,
                        data_key="lng",
                        allow_none=True,
                        validate=[validate.Range(-180, 180)],
                        comment="经度",
                    ),
                    "latitude": fields.Decimal(
                        required=False,
                        data_key="lat",
                        allow_none=True,
                        validate=[validate.Range(-90, 90)],
                        comment="纬度",
                    ),
                    "realname": fields.String(
                        required=False,
                        allow_none=True,
                        validate=[validate.Length(0, 32)],
                        comment="历史真实姓名",
                    ),
                },
                required=True,
                comment="店铺信息",
                unknown=True,
            ),
        },
        location="json",
    )
    def post(self, request, args):

        user_id = args["user_id"]
        user = get_user_by_id_interface(user_id)
        serializer = ShopCreateSerializer(data=args.get("shop_data"), context={'user':user})
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success(data=serializer.data)

    @use_args(
        {
            "shop_id": fields.Integer(required=True, comment="森果通行证ID"),
        },
        location="query"
    )
    def get(self, request, args):
        shop_id = args.get("shop_id")
        shop = get_shop_by_shop_id(shop_id)
        if not shop:
            return self.send_fail(error_text="店铺不存在")
        shop = Shop.objects.get(id=shop_id)
        super_admin_data = get_user_by_id_interface(shop.super_admin.id)
        shop.super_admin_data = super_admin_data
        serializer = SuperShopSerializer(shop)
        return self.send_success(data=serializer.data)


class SuperShopListView(UserBaseView):
    """总后台-商铺-商铺列表"""

    def get(self, request):
        user = self.current_user
        # 根据用户信息查找到对应的员工及所属店铺信息
        staff_list = list_staff_by_user_id_interface(user.id, roles=StaffRole.SHOP_ADMIN)
        if not staff_list:
            return self.send_success(data_list=[])
        # 根据查到的店铺信息找到对应店铺的信息
        shop_ids = [sl.shop_id for sl in staff_list]
        shop_list = list_shop_by_shop_ids(shop_ids)
        # 查找所有店铺的商品数量
        shop_id_2_product_count = get_shop_product_species_count_by_shop_ids(shop_ids)
        # 添加额外属性
        for sl in shop_list:
            sl.product_species_count = shop_id_2_product_count.get(sl.id, 0)
            sl.is_super_admin = 1 if sl.super_admin_id == user.id else 0
        serializer = SuperShopListSerializer(shop_list, many=True)
        return self.send_success(data_list=serializer.data)


class SuperShopStatusView(UserBaseView):
    """总后台-通过shop_status查询所有的店铺&修改店铺的shop_status"""
    pagination_class = StandardResultsSetPagination

    # 弄个假的操作人信息
    class Operator:
        operate_id = 1
        operate_name = ""
        operate_img = ""

    @use_args(
        {
            "shop_status": fields.Integer(
                required=True,
                validate=[
                    validate.OneOf(
                        [ShopStatus.CHECKING, ShopStatus.NORMAL, ShopStatus.REJECTED]
                    )
                ],
                comment="店铺状态",
            ),
        },
        location="query"
    )
    def get(self, request, args):
        shop_status = args.get("shop_status")
        shop_list = list_shop_by_shop_status(shop_status)
        # 店铺创建者信息, 与店铺ID
        creator_ids = set()
        shop_ids = set()
        for slq in shop_list:
            creator_ids.add(slq.super_admin_id)
            shop_ids.add(slq.id)
        creator_ids = list(creator_ids)
        shop_ids = list(shop_ids)
        # 店铺创建者
        creator_list = list_user_by_ids_interface(creator_ids)
        creator_id_2_creator = {clq.id: clq for clq in creator_list}
        # 历史真实姓名
        shop_realname_list = list_shop_creator_history_realname(shop_ids)
        shop_realname_map = {srl.id: srl.realname for srl in shop_realname_list}
        if shop_status == ShopStatus.CHECKING:
            for slq in shop_list:
                slq.creator = creator_id_2_creator.get(slq.super_admin_id)
                slq.current_realname = shop_realname_map.get(slq.id, "")
        elif shop_status == ShopStatus.NORMAL:
            for slq in shop_list:
                slq.creator = creator_id_2_creator.get(slq.super_admin_id)
                slq.current_realname = shop_realname_map.get(slq.id, "")
                slq.operator = self.Operator
        else:
            reject_reason_list = list_shop_reject_reason(shop_ids)
            shop_id_2_reject_reason = {
                rrl.id: rrl.reject_reason for rrl in reject_reason_list
            }
            for slq in shop_list:
                slq.creator = creator_id_2_creator.get(slq.super_admin_id)
                slq.current_realname = shop_realname_map.get(slq.id, "")
                slq.operator = self.Operator
                slq.reject_reason = shop_id_2_reject_reason.get(slq.id, "")
        shop_list = self._get_paginated_data(shop_list, SuperShopStatusSerializer)
        return self.send_success(data_list=shop_list)

    @use_args(
        {
            "shop_id": fields.Integer(
                required=True, validate=[validate.Range(0)], comment="店铺ID"
            ),
            "shop_status": fields.Integer(
                required=True,
                validate=[validate.OneOf([ShopStatus.NORMAL, ShopStatus.REJECTED])],
                comment="店铺状态",
            ),
            "reject_reason": fields.String(
                required=False,
                missing="",
                validate=[validate.Length(0, 200)],
                comment="拒绝理由,尽在拒绝的时候需要",
            ),
        },
        location="json",
    )
    def put(self, request, args):
        shop_id = args.pop("shop_id")
        shop = get_shop_by_shop_id(shop_id)
        if not shop:
            return self.send_fail(error_text="店铺不存在")
        # 更改店铺状态
        serializer = SuperShopStatusSerializer(shop, data=args)
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success()


class SuperShopVerifyView(UserBaseView):
    """总后台-修改店铺认证状态"""

    @use_args(
        {
            "shop_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="店铺ID"
            ),
            "verify_status": fields.Integer(
                required=True,
                validate=[
                    validate.OneOf(
                        [
                            ShopVerifyActive.YES,
                            ShopVerifyActive.CHECKING,
                            ShopVerifyActive.REJECTED,
                        ]
                    )
                ],
                comment="店铺认证状态",
            ),
            "verify_type": fields.Integer(
                required=True,
                validate=[
                    validate.OneOf(
                        [ShopVerifyType.ENTERPRISE, ShopVerifyType.INDIVIDUAL]
                    )
                ],
                comment="店铺认证类型,个人/企业",
            ),
            "verify_content": fields.String(
                required=True, validate=[validate.Length(0, 200)], comment="认证内容"
            ),
        },
        location="json"
    )
    def put(self, request, args):
        shop = get_shop_by_shop_id(args.pop("shop_id"))
        if not shop:
            return self.send_fail(error_text="店铺不存在")
        serializer = SuperShopVerifySerializer(shop, data=args)
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success()


class AdminShopView(AdminBaseView):
    """商户后台-商铺-获取当前店铺与用户信息"""

    def get(self, request):
        user = self.current_user
        shop = self.current_shop
        staff = self.current_staff
        staff_personal_data = {_:getattr(user, _)for _ in USER_OUTPUT_CONSTANT}
        staff.staff_personal_data = staff_personal_data
        shop_serializer = AdminShopSerializer(shop)
        staff_serializer = StaffSerializer(staff)
        return self.send_success(shop_data=shop_serializer.data, staff_data=staff_serializer.data)


class MallShopView(MallBaseView):
    """商城端-商铺-获取当前店铺信息"""

    def get(self, request, shop_code):
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        user = self.current_user
        shop_serializer = MallShopSerializer(shop)
        customer_serializer = UserSerializer(user)
        # 额外查询用户的积分数据
        customer = get_customer_by_user_id_and_shop_id_interface(user.id, shop.id)
        customer_info = dict(customer_serializer.data)
        shop_info = dict(shop_serializer.data)
        customer_info["points"] = round(float(customer.point), 2) if customer else 0
        customer_info["is_new_customer"] = (
            customer.is_new_customer() if customer else True
        )
        return self.send_success(shop_data=shop_info, user_data=customer_info)







