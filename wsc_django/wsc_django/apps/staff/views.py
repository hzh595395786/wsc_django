from rest_framework import status
from rest_framework.response import Response

from staff.constant import StaffApplyStatus
from staff.models import StaffApply
from staff.serializers import (
    StaffDetailSerializer,
    StaffApplyCreateSerializer,
    StaffApplyDetailSerializer,
)
from staff.services import (
    get_staff_by_user_id_and_shop_id,
    get_staff_apply_by_user_id_and_shop_id,
)
from wsc_django.utils.views import StaffBaseView, MallBaseView


class AdminStaffView(StaffBaseView):
    """商城端-员工增删改查"""

    serializer_class = StaffDetailSerializer


class StaffApplyView(MallBaseView):
    """商城端-提交员工申请&获取申请信息"""

    def get_tmp_class(self, status):
        """获取一个员工申请模板类"""
        class TMP:
            def __init__(self, status):
                self.status = status
        return TMP(status)

    def get(self, request, shop_code):
        user = request.user
        self._set_current_shop(request, shop_code)
        current_shop = request.shop
        if not current_shop:
            return Response(status=status.HTTP_404_NOT_FOUND)
        staff_apply_query = get_staff_apply_by_user_id_and_shop_id(user.id, current_shop.id)
        # 没有审核记录的是超管或者第一次申请的人
        if not staff_apply_query:
            # 超管
            if current_shop.super_admin_id == user.id:
                staff_apply_query = self.get_tmp_class(StaffApplyStatus.PASS)
            else:
                staff_apply_query = self.get_tmp_class(StaffApplyStatus.UNAPPlY)
        staff_apply_query.user_info = user
        serializer = StaffApplyDetailSerializer(staff_apply_query)
        return self.send_success(data=serializer.data, shop_info={"shop_name":current_shop.shop_name})

    def post(self, request, shop_code):
        user = request.user
        self._set_current_shop(request, shop_code)
        current_shop = request.shop
        if not current_shop:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # 验证员工是否存在
        staff = get_staff_by_user_id_and_shop_id(user.id, current_shop.id)
        if staff:
            return self.send_fail(error_text="已经为该店铺的员工")
        # 验证是否已经提交申请
        staff_apply = get_staff_apply_by_user_id_and_shop_id(user.id, current_shop.id)
        if staff_apply:
            return self.send_fail(error_text="已提交申请，无需重复提交")
        serializer = StaffApplyCreateSerializer(data=request.data, context={'request':request})
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

