from rest_framework import status
from rest_framework.response import Response

from staff.constant import StaffApplyStatus, StaffRole, StaffStatus
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
    list_staff_by_shop_id)
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import StaffBaseView, MallBaseView, AdminBaseView


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
        staff_apply_query = get_staff_apply_by_user_id_and_shop_id(user.id, current_shop.id)
        # 没有审核记录的是超管或者第一次申请的人
        if not staff_apply_query:
            # 超管
            if current_shop.super_admin_id == user.id:
                staff_apply_query = self.get_tmp_class(StaffApplyStatus.PASS)
            else:
                staff_apply_query = self.get_tmp_class(StaffApplyStatus.UNAPPlY)
        staff_apply_query.user_info = user
        serializer = StaffApplySerializer(staff_apply_query)
        return self.send_success(data=serializer.data, shop_info={"shop_name":current_shop.shop_name})

    def post(self, request, shop_code):
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
        serializer = StaffApplyCreateSerializer(data=request.data, context={'self':self})
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
    def post(self, request):
        shop_id = self.current_shop.id
        staff_apply_id = request.data.pop("staff_apply_id", 0)
        staff_apply = get_staff_apply_by_shop_id_and_id(shop_id, staff_apply_id)
        if not staff_apply:
            return self.send_fail(error_text='员工申请记录不存在')
        staff_apply_serializer = StaffApplySerializer(staff_apply, request.data)
        # 此处无需验证，仅为了save的执行
        staff_apply_serializer.is_valid()
        staff_apply_serializer.save()
        # 申请通过，创建员工
        staff_info = {"shop_id": shop_id, "user_id": staff_apply.user.id}
        staff_info.update(request.data)
        # 校验员工是否存在
        staff = get_staff_by_user_id_and_shop_id(
            staff_apply.user.id, shop_id, filter_delete=False
        )
        if not staff:
            staff_serializer = StaffSerializer(data=staff_info)
            if not staff_serializer.is_valid():
                return Response(data=staff_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            staff_serializer.save()
        elif staff.status == StaffStatus.NORMAL:
            return self.send_fail(error_text="已经为该店铺的员工")
        else:
            # 员工状态为被删除，则将状态修改为正常
            staff_info["status"] = StaffStatus.NORMAL
            for k, v in staff_info.items():
                setattr(staff, k, v)
            staff.save()
        return self.send_success()



class AdminStaffView(AdminBaseView):
    """商城端-员工-员工详情&编辑员工&删除员工"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    def get(self, request):
        staff_id = request.query_params.get("staff_id", 0)
        shop_id = self.current_shop
        staff = get_staff_by_id_and_shop_id(staff_id, shop_id)
        if not staff:
            return self.send_fail(error_text="员工不存在")
        serializer = StaffSerializer(staff)
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    def delete(self, request):
        staff_id = request.query_params.get("staff_id", 0)
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
        return self.send_success()

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    def post(self, request):
        staff_id = request.data.pop("staff_id", 0)
        shop_id = self.current_shop.id
        staff = get_staff_by_id_and_shop_id(staff_id, shop_id)
        if not staff:
            return self.send_fail(error_text="员工不存在")
        # 超管仅自己可以编辑,而且权限不可编辑
        elif staff.roles == StaffRole.SHOP_SUPER_ADMIN:
            if self.current_user.id != staff.user_id:
                return self.send_fail(error_text="超管信息仅自己可以编辑")
        serializer = StaffSerializer(staff, data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.send_success()


class AdminStaffListView(AdminBaseView):
    """后台-员工-员工列表"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_STAFF])
    def get(self, request):
        shop_id = self.current_shop.id
        staff_list = list_staff_by_shop_id(shop_id, request.query_params.get("keyword", None))
        staff_list = self._get_paginated_data(staff_list, StaffSerializer)
        return self.send_success(data_list=staff_list)
