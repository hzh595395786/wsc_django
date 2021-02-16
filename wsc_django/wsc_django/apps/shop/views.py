from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Shop
from staff.constant import StaffRole
from wsc_django.utils.authenticate import WSCAuthenticate
from wsc_django.utils.setup import get_format_response_data
from shop.serializers import (
    ShopCreateSerializer,
    ShopDetailSerializer,
    ShopListSerializer,
)
from shop.services import (
    get_shop_by_shop_id,
    list_shop_by_shop_ids,
)
from shop.interface import (
    list_staff_by_user_id_interface,
)


class ShopView(APIView):
    """商城端-商铺创建&商铺详情"""
    # authentication_classes = [WSCAuthenticate]

    def post(self, request):
        serializer = ShopCreateSerializer(data=request.data, context={'request':request})
        if not serializer.is_valid():
            return Response({'message':"缺少参数或参数有误"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        data = get_format_response_data(serializer.data, True)
        return Response(data=data)

    def get(self, request):
        shop_id = request.query_params.get("shop_id", None)
        if not shop_id:
            return Response({'message':"缺少参数或参数有误"}, status=status.HTTP_400_BAD_REQUEST)
        shop = get_shop_by_shop_id(shop_id)
        if not shop:
            return Response({'message':"店铺不存在"}, status=status.HTTP_404_NOT_FOUND)
        shop = Shop.objects.get(id=shop_id)
        serializer = ShopDetailSerializer(shop)
        data = get_format_response_data(serializer.data, True)
        return Response(data=data)


class ShopListView(APIView):
    """商城端-商铺列表"""

    def get(self, request):
        user = request.user
        # 根据用户信息查找到对应的员工及所属店铺信息
        staff_list = list_staff_by_user_id_interface(user.id, roles=StaffRole.SHOP_ADMIN)
        if not staff_list:
            data = get_format_response_data({"data":''}, True)
            return Response(data=data)
        # 根据查到的店铺信息找到对应店铺的信息
        shop_ids = [sl.shop_id for sl in staff_list]
        shop_list = list_shop_by_shop_ids(shop_ids)
        # 获取商铺的超管id列表
        super_admin_ids = [sl.super_admin_id for sl in shop_list]
        # 查找所有店铺的商品数量，todo 待写
        # 添加额外属性
        for sl in shop_list:
            sl.is_super_admin = 1 if sl.super_admin_id == user.id else 0
        serializer = ShopListSerializer(shop_list, many=True)
        data = get_format_response_data(serializer.data, True, many=True)
        return Response(data=data)




