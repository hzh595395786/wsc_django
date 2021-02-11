from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from wsc_django.utils.setup import get_format_response_data
from staff.models import StaffApply
from staff.serializers import (
    StaffDetailSerializer,
    StaffApplyCreateSerializer,
)
from staff.services import (
    get_staff_by_user_id_and_shop_id,
    get_staff_apply_by_user_id_and_shop_id,
)



class AdminStaffView(APIView):
    """商城端-员工增删改查"""

    serializer_class = StaffDetailSerializer


class StaffApplyView(APIView):
    """商城端-提交员工申请&获取申请信息"""

    def get(self, request):
        user = request.user
        shop = request.shop
        return Response()

    def post(self, request):
        user = request.user
        shop = request.shop
        # 验证员工是否存在
        staff = get_staff_by_user_id_and_shop_id(user.id, shop.id)
        if staff:
            data = get_format_response_data({"error_text":"员工已存在"}, False)
            return Response(data=data)
        # 验证是否已经提交申请
        staff_apply = get_staff_apply_by_user_id_and_shop_id(user.id, shop.id)
        if staff_apply:
            data = get_format_response_data({"error_text":"申请已提交，无需重复提交"}, False)
            return Response(data=data)
        serializer = StaffApplyCreateSerializer(data=request.data, context={'request':request})
        if not serializer.is_valid():
            return Response({'message': "缺少参数或参数有误"}, status=status.HTTP_400_BAD_REQUEST)
        staff_apply = serializer.save()
        data = {
            "staff_apply_id": staff_apply.id,
            "status": staff_apply.status,
            "expired": staff_apply.expired,
            "user_id": staff_apply.user_id
        }
        data = get_format_response_data(data, True)
        return Response(data=data)

