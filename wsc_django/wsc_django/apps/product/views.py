from rest_framework import status
from rest_framework.response import Response

from product.services import get_product_with_group_name
from wsc_django.utils.views import AdminBaseView
from product.serializers import (
    ProductCreateSerializer,
    AdminProductSerializer,
)


class AdminProductView(AdminBaseView):
    """后台-货品-货品创建&单个货品详情"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data, context={'self':self})
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def get(self, request):
        current_shop = self.current_shop
        product_id = request.query_params.get("product_id", None)
        if not product_id:
            return Response(data={"error_text":"缺少product_id"}, status=status.HTTP_400_BAD_REQUEST)
        product = get_product_with_group_name(current_shop.id, product_id)
        if not product:
            return self.send_fail(error_text="货品不存在")
        serializer = AdminProductSerializer(product)
        return self.send_success(data=serializer.data)


