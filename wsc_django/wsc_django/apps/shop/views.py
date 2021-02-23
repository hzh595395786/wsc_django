from rest_framework import status
from rest_framework.response import Response

from shop.models import Shop
from staff.constant import StaffRole
from staff.serializers import StaffDetailSerializer
from user.constant import USER_OUTPUT_CONSTANT
from user.serializers import UserSerializer
from wsc_django.utils.views import UserBaseView, AdminBaseView, MallBaseView
from shop.serializers import (
    ShopCreateSerializer,
    SuperShopSerializer,
    SuperShopListSerializer,
    AdminShopSerializer,
    MallShopSerializer,
)
from shop.services import (
    get_shop_by_shop_id,
    list_shop_by_shop_ids,
    get_shop_product_species_count_by_shop_ids,
)
from shop.interface import (
    list_staff_by_user_id_interface,
    get_user_by_id_interface,
    get_customer_by_user_id_and_shop_id_interface
)


class SuperShopView(UserBaseView):
    """总后台-商铺-商铺创建&商铺详情"""

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


class AdminShopView(AdminBaseView):
    """商户后台-商铺-获取当前店铺与用户信息"""

    def get(self, request):
        user = self.current_user
        shop = self.current_shop
        staff = self.current_staff
        staff_personal_data = {_:getattr(user, _)for _ in USER_OUTPUT_CONSTANT}
        staff.staff_personal_data = staff_personal_data
        shop_serializer = AdminShopSerializer(shop)
        staff_serializer = StaffDetailSerializer(staff)
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







