from rest_framework import status
from rest_framework.response import Response

from shop.models import Shop
from staff.constant import StaffRole
from wsc_django.utils.authenticate import WSCAuthenticate
from wsc_django.utils.views import GlobalBaseView
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
    get_user_by_id_interface,
)


class ShopView(GlobalBaseView):
    """商城端-商铺创建&商铺详情"""
    # authentication_classes = [WSCAuthenticate]

    def post(self, request):
        user_id = request.data.get("user_id", None)
        if not user_id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        user = get_user_by_id_interface(user_id)
        serializer = ShopCreateSerializer(data=request.data.get("shop_data"), context={'user':user})
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.send_success(data=serializer.data)

    def get(self, request):
        shop_id = request.query_params.get("shop_id", None)
        if not shop_id:
            return self.send_fail(error_text="缺少shop_id")
        shop = get_shop_by_shop_id(shop_id)
        if not shop:
            return self.send_fail(error_text="店铺不存在")
        shop = Shop.objects.get(id=shop_id)
        serializer = ShopDetailSerializer(shop)
        return self.send_success(data=serializer.data)


class ShopListView(GlobalBaseView):
    """商城端-商铺列表"""

    def get(self, request):
        user = request.user
        # 根据用户信息查找到对应的员工及所属店铺信息
        staff_list = list_staff_by_user_id_interface(user.id, roles=StaffRole.SHOP_ADMIN)
        if not staff_list:
            return self.send_success(data_list=[])
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
        return Response(self.send_success(data_list=serializer.data))




