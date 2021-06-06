from rest_framework import status
from rest_framework.response import Response
from webargs import fields, validate
from webargs.djangoparser import use_args

from logs.constant import StaffLogType
from staff.constant import StaffApplyStatus, StaffRole, StaffStatus
from staff.interface import create_staff_log_interface
from staff.serializers import (
    StaffSerializer,
    StaffApplyCreateSerializer,
    StaffApplySerializer,
)
from staff.services import (
    get_staff_by_id_and_shop_id,
    get_staff_apply_by_shop_id_and_id,
    get_staff_by_user_id_and_shop_id,
    get_staff_apply_by_user_id_and_shop_id,
    list_staff_apply_by_shop_id,
    expire_staff_apply_by_staff,
    list_staff_by_shop_id,
    cal_all_roles_without_super,
    cal_all_permission,
)
from wsc_django.utils.constant import PHONE_RE
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import StaffBaseView, MallBaseView, AdminBaseView

all_roles = cal_all_roles_without_super()
all_permission = cal_all_permission()


class StaffApplyView(MallBaseView):
    """后台-员工-提交员工申请&获取申请信息"""

    def get_tmp_class(self, status):
        """获取一个员工申请模板类"""
        class TMP:
            def __init__(self, status):
                self.status = status
        return TMP(status)

    def get(self, request, shop_code):
        user = self.current_user
        self._set_current_shop(request, shop_code)
        current_shop = self.current_shop
        staff_apply = get_staff_apply_by_user_id_and_shop_id(user.id, current_shop.id)
        # 没有审核记录的是超管或者第一次申请的人
        if not staff_apply:
            # 超管
            if current_shop.super_admin_id == user.id:
                staff_apply = self.get_tmp_class(StaffApplyStatus.PASS)
            else:
                staff_apply = self.get_tmp_class(StaffApplyStatus.UNAPPlY)
        serializer = StaffApplySerializer(staff_apply)
        return self.send_success(data=serializer.data, shop_info={"shop_name":current_shop.shop_name})

    @use_args(
        {
            "realname": fields.String(
                required=True, validate=[validate.Length(1, 64)], comment="真实姓名"
            ),
            "phone": fields.String(
                required=False,
                validate=[validate.Regexp(PHONE_RE)],
                comment="手机号,已绑定的时候是不需要的",
            ),
            "code": fields.String(
                required=False, validate=[validate.Regexp(r"^[0-9]{4}$")], comment="验证码"
            ),
            "birthday": fields.Date(required=False, allow_none=True, comment="生日"),
        },
        location="json"
    )
    def post(self, request, args, shop_code):
        user = self.current_user
        self._set_current_shop(request, shop_code)
        current_shop = self.current_shop
        # 验证员工是否存在
        staff = get_staff_by_user_id_and_shop_id(user.id, current_shop.id)
        if staff:
            return self.send_fail(error_text="已经为该店铺的员工")
        # 验证是否已经提交申请
        staff_apply = get_staff_apply_by_user_id_and_shop_id(user.id, current_shop.id)
        if staff_apply:
            return self.send_fail(error_text="已提交申请，无需重复提交")
        serializer = StaffApplyCreateSerializer(data=args, context={'self':self})
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        staff_apply = serializer.save()
        data = {
            "staff_apply_id": staff_apply.id,
            "status": staff_apply.status,
            "expired": staff_apply.expired,
            "user_id": staff_apply.user_id
        }
        return self.send_success(data=data)


class AdminStaffApplyView(AdminBaseView):
    """后台-员工-申请列表&通过员工申请"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    def get(self, request):
        shop_id = self.current_shop.id
        staff_apply_list = list_staff_apply_by_shop_id(shop_id)
        staff_apply_list = self._get_paginated_data(staff_apply_list, StaffApplySerializer)
        return self.send_success(data_list=staff_apply_list)

    @StaffBaseView.permission_required([StaffBaseView.staff_permissions.ADMIN_STAFF])
    @use_args(
        {
            "staff_apply_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="申请ID"
            ),
            "position": fields.String(
                required=False,
                validate=[validate.Length(0, 16)],
                allow_none=True,
                comment="员工职位",
            ),
            "entry_date": fields.Date(required=False, allow_none=True, comment="入职日期"),
            "remark": fields.String(
                required=False,
                validate=[validate.Length(0, 20)],
                allow_none=True,
                comment="备注",
            ),
            "roles": fields.Integer(
                required=True, validate=[validate.Range(1, all_roles)], comment="角色"
            ),
            "permissions": fields.Integer(
                required=True,
                validate=[validate.Range(1, all_permission)],
                comment="权限",
            )
        },
        location="json"
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        staff_apply_id = args.pop("staff_apply_id")
        staff_apply = get_staff_apply_by_shop_id_and_id(shop_id, staff_apply_id)
        if not staff_apply:
            return self.send_fail(error_text='员工申请记录不存在')
        staff_apply_serializer = StaffApplySerializer(staff_apply, args)
        # 此处无需验证，仅为了save的执行
        staff_apply_serializer.is_valid()
        staff_apply_serializer.save()
        # 申请通过，创建员工
        staff_info = {"shop_id": shop_id, "user_id": staff_apply.user.id}
        staff_info.update(args)
        # 校验员工是否存在
        staff = get_staff_by_user_id_and_shop_id(
            staff_apply.user.id, shop_id, filter_delete=False
        )
        if not staff:
            staff_serializer = StaffSerializer(data=staff_info)
            if not staff_serializer.is_valid():
                return self.send_error(
                    error_message=staff_serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
                )
            staff = staff_serializer.save()
        elif staff.status == StaffStatus.NORMAL:
            return self.send_fail(error_text="已经为该店铺的员工")
        else:
            # 员工状态为被删除，则将状态修改为正常
            staff_info["status"] = StaffStatus.NORMAL
            for k, v in staff_info.items():
                setattr(staff, k, v)
            staff.save()
        # 创建操作日志
        log_info = {
            "shop_id": shop_id,
            "operator_id": self.current_user.id,
            "operate_type": StaffLogType.ADD_STAFF,
            "staff_id": staff.id,
        }
        create_staff_log_interface(log_info)
        return self.send_success(staff_id=staff.id)


class AdminStaffView(AdminBaseView):
    """商城端-员工-员工详情&编辑员工&删除员工"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    @use_args(
        {
            "staff_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="员工ID"
            )
        },
        location="query"
    )
    def get(self, request, args):
        staff_id = args.get("staff_id")
        shop_id = self.current_shop
        staff = get_staff_by_id_and_shop_id(staff_id, shop_id)
        if not staff:
            return self.send_fail(error_text="员工不存在")
        serializer = StaffSerializer(staff)
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    @use_args(
        {
            "staff_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="员工ID"
            )
        },
        location="json"
    )
    def delete(self, request, args):
        staff_id = args.get("staff_id")
        shop_id = self.current_shop.id
        staff = get_staff_by_id_and_shop_id(staff_id, shop_id)
        if not staff:
            return self.send_fail(error_text="员工不存在")
        elif staff.roles == StaffRole.SHOP_SUPER_ADMIN:
            return self.send_fail(error_text="超管不可删除")
        # 使其申请记录过期,可以再次申请
        expire_staff_apply_by_staff(staff.shop.id, staff.user.id)
        # 假删除
        staff.status = StaffStatus.DELETED
        staff.save()
        # 创建操作日志
        log_info = {
            "shop_id": shop_id,
            "operator_id": self.current_user.id,
            "operate_type": StaffLogType.DELETE_STAFF,
            "staff_id": staff.id,
        }
        create_staff_log_interface(log_info)
        return self.send_success()

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    @use_args(
        {
            "staff_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="员工ID"
            ),
            "position": fields.String(
                required=False,
                validate=[validate.Length(0, 16)],
                allow_none=True,
                comment="员工职位",
            ),
            "entry_date": fields.Date(required=False, allow_none=True, comment="入职日期"),
            "remark": fields.String(
                required=False,
                validate=[validate.Length(0, 20)],
                allow_none=True,
                comment="备注",
            ),
            "roles": fields.Integer(
                required=True, validate=[validate.Range(0, all_roles)], comment="角色"
            ),
            "permissions": fields.Integer(
                required=True,
                validate=[validate.Range(0, all_permission)],
                comment="权限",
            ),
        },
        location="json"
    )
    def put(self, request, args):
        staff_id = args.pop("staff_id")
        shop_id = self.current_shop.id
        staff = get_staff_by_id_and_shop_id(staff_id, shop_id)
        if not staff:
            return self.send_fail(error_text="员工不存在")
        # 超管仅自己可以编辑,而且权限不可编辑
        elif staff.roles == StaffRole.SHOP_SUPER_ADMIN:
            if self.current_user.id != staff.user_id:
                return self.send_fail(error_text="超管信息仅自己可以编辑")
        serializer = StaffSerializer(staff, data=args)
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success()


class AdminStaffListView(AdminBaseView):
    """后台-员工-员工列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    @use_args(
        {
            "keyword": fields.String(required=False, comment="搜索关键字(姓名或手机号)"),
            "page": fields.Integer(required=False, missing=1, comment="页码"),
            "page_size": fields.Integer(
                required=False, missing=20, validate=[validate.Range(1)], comment="每页条数"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        page = args.get("page")
        shop_id = self.current_shop.id
        staff_list = list_staff_by_shop_id(shop_id, args.get("keyword"))
        # page为-1时,不分页
        if page > 0:
            staff_list = self._get_paginated_data(staff_list, StaffSerializer)
        else:
            # 适配前端参数要求
            staff_list = {'results': StaffSerializer(staff_list, many=True).data}
        return self.send_success(data_list=staff_list)
