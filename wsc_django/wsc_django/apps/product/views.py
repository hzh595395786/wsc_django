from rest_framework import status
from rest_framework.response import Response

from product.constant import ProductStatus, ProductOperationType
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.setup import is_contains, str_to_list
from wsc_django.utils.views import AdminBaseView
from product.interface import list_order_with_order_lines_by_product_id_interface
from product.serializers import (
    ProductCreateSerializer,
    AdminProductSerializer,
    AdminProductGroupSerializer,
    AdminProductSaleRecordSerializer,
)
from product.services import (
    get_product_by_id,
    list_product_by_ids,
    update_products_status,
    list_product_by_filter,
    sort_shop_product_group,
    get_product_with_group_name,
    delete_product_by_ids_and_shop_id,
    update_product_product_group_by_ids,
    get_product_group_by_shop_id_and_id,
    list_product_group_with_product_count,
    delete_product_group_by_id_and_shop_id,
)


class AdminProductView(AdminBaseView):
    """后台-货品-货品创建&货品详情&编辑货品&批量删除货品"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def post(self, request):
        group_id = request.data.get("group_id", 0)
        product_group = get_product_group_by_shop_id_and_id(self.current_shop.id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        serializer = ProductCreateSerializer(data=request.data, context={'self':self})
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def get(self, request):
        current_shop = self.current_shop
        product_id = request.query_params.get("product_id", None)
        if not product_id:
            return self.send_error(
                error_message={"error_text":"缺少product_id"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        product = get_product_with_group_name(current_shop.id, product_id)
        if not product:
            return self.send_fail(error_text="货品不存在")
        serializer = AdminProductSerializer(product)
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def put(self, request):
        shop_id = self.current_shop.id
        product_id = request.data.pop("product_id", 0)
        product = get_product_by_id(shop_id, product_id)
        if not product:
            return self.send_fail(error_text="货品不存在")
        group_id = request.data.pop("group_id", 0)
        product_group = get_product_group_by_shop_id_and_id(shop_id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        serializer = AdminProductSerializer(product, data=request.data, context={"self":self})
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def delete(self, request):
        product_ids = request.data.get("product_ids", [])
        if not product_ids:
            return self.send_error(
                error_message={"message":"缺少product_ids"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        ret, info = delete_product_by_ids_and_shop_id(product_ids, self.current_shop.id)
        if not ret:
            return self.send_fail(error_text=info)
        else:
            return self.send_success()


class AdminProductsView(AdminBaseView):
    """后台-货品-获取货品列表&批量修改货品(上架，下架)"""
    pagination_class = StandardResultsSetPagination
    default_status_list = [ProductStatus.ON, ProductStatus.OFF]
    product_status_list = [ProductStatus.ON, ProductStatus.OFF]
    product_operation_list = [ProductOperationType.ON, ProductOperationType.OFF]

    def get(self, request):
        shop = self.current_shop
        ret, status_list = str_to_list(request.query_params.get("status"), default=self.default_status_list)
        if not ret:
            return self.send_error(error_message=status_list, status_code=status.HTTP_400_BAD_REQUEST)
        ret = is_contains(status_list, self.product_status_list)
        if not ret:
            return self.send_error(status_code=status.HTTP_400_BAD_REQUEST)
        group_id = request.query_params.get("group_id", 0)
        keyword = request.query_params.get("keyword", None)
        product_list = list_product_by_filter(shop.id, status_list, keyword, group_id)
        product_list = self._get_paginated_data(product_list, AdminProductSerializer)
        return self.send_success(data_list=product_list)

    def put(self, request):
        operation_type = request.data.get("operation_type", 0)
        if operation_type not in self.product_operation_list:
            return self.send_error(
                error_message={'messages': "操作类型有误"},status_code=status.HTTP_400_BAD_REQUEST
            )
        product_ids = request.data.get("product_ids", None)
        if not product_ids:
            return self.send_error(
                error_message={'messages': "product_ids为空"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        product_list = list_product_by_ids(self.current_shop.id, product_ids)
        update_products_status(product_list, operation_type)
        return self.send_success()


class AdminProductGroupsView(AdminBaseView):
    """后台-货品-批量更新货品分组"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def put(self, request):
        shop = self.current_shop
        group_id = request.data.get("group_id", 0)
        product_ids = request.data.pop("product_ids", [])
        if not product_ids:
            return self.send_error(
                error_message={"message": "缺少product_ids"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        # 校验分组是否存在
        product_group = get_product_group_by_shop_id_and_id(shop.id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        # 获取货品,更新货品信息
        update_product_product_group_by_ids(product_ids, group_id)
        return self.send_success()


class AdminProductGroupView(AdminBaseView):
    """后台-货品-添加货品分组&编辑货品分组&删除货品分组&获取货品分组列表"""
    default_status_list = [ProductStatus.ON, ProductStatus.OFF]
    product_status_list = [ProductStatus.ON, ProductStatus.OFF]

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def post(self, request):
        serializer = AdminProductGroupSerializer(data=request.data, context={"self":self})
        if not serializer.is_valid():
            return self.send_error(status_code=status.HTTP_400_BAD_REQUEST, error_message=serializer.errors)
        serializer.save()
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def put(self, request):
        group_id = request.data.pop("group_id", 0)
        shop = self.current_shop
        product_group = get_product_group_by_shop_id_and_id(shop.id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        serializer = AdminProductGroupSerializer(product_group, data=request.data)
        if not serializer.is_valid():
            return self.send_error(error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.send_success()

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def delete(self, request):
        shop = self.current_shop
        group_id = request.data.get("group_id", 0)
        product_group = get_product_group_by_shop_id_and_id(shop.id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        ret, info = delete_product_group_by_id_and_shop_id(group_id, shop.id)
        if not ret:
            return self.send_fail(error_text=info)
        else:
            return self.send_success()

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def get(self, request):
        shop = self.current_shop
        ret, status_list = str_to_list(request.query_params.get("status"), default=self.default_status_list)
        if not ret:
            return self.send_error(error_message=status_list, status_code=status.HTTP_400_BAD_REQUEST)
        ret = is_contains(status_list, self.product_status_list)
        if not ret:
            return self.send_error(status_code=status.HTTP_400_BAD_REQUEST)
        product_group_with_count = list_product_group_with_product_count(shop.id, status_list)
        serializer = AdminProductGroupSerializer(product_group_with_count, many=True)
        return self.send_success(data_list=serializer.data)


class AdminProductGroupSortView(AdminBaseView):
    """后台-货品-分组排序"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def post(self, request):
        group_ids = request.data.get("group_ids", [])
        if not group_ids:
            return self.send_error(
                error_message={"message": "缺少group_ids"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        shop = self.current_shop
        sort_shop_product_group(shop.id, group_ids)
        return self.send_success()


class AdminProductSaleRecordView(AdminBaseView):
    """后台-货品-货品详情-获取货品销售记录"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def get(self, request):
        product_id = request.query_params.get("product_id", None)
        if not product_id or product_id == 0:
            return self.send_error(
                error_message={'messages': "product_id有误或不存在"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        shop = self.current_shop
        product_sale_record_list = list_order_with_order_lines_by_product_id_interface(shop.id, product_id)
        product_sale_record_list = self._get_paginated_data(
            product_sale_record_list, AdminProductSaleRecordSerializer
        )
        return self.send_success(data_list=product_sale_record_list)

