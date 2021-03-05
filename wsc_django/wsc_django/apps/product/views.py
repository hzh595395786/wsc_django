from rest_framework import status
from rest_framework.response import Response
from webargs.djangoparser import use_args
from webargs import fields, validate

from product.constant import ProductStatus, ProductOperationType
from wsc_django.utils.arguments import StrToList
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView, MallBaseView
from product.interface import list_order_with_order_lines_by_product_id_interface
from product.serializers import (
    MallProductSerializer,
    ProductCreateSerializer,
    AdminProductSerializer,
    MallProductGroupSerializer,
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
    list_product_group_with_product_list,
    list_product_group_with_product_count,
    delete_product_group_by_id_and_shop_id,
)


class AdminProductView(AdminBaseView):
    """后台-货品-货品创建&货品详情&编辑货品&批量删除货品"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "name": fields.String(
                required=True, validate=[validate.Length(1, 15)], comment="货品名"
            ),
            "group_id": fields.Integer(required=True, comment="分组id"),
            "price": fields.Decimal(
                required=True,
                validate=[validate.Range(0, min_inclusive=False)],
                comment="货品单价",
            ),
            "storage": fields.Decimal(
                required=True, validate=[validate.Range(0)], comment="商品库存"
            ),
            "code": fields.String(required=False, comment="货品编码"),
            "summary": fields.String(
                required=False, validate=[validate.Length(0, 20)], comment="货品简介"
            ),
            "pictures": fields.List(
                fields.String(),
                required=False,
                validate=[validate.Length(1, 5)],
                comment="轮播图",
            ),
            "description": fields.String(required=False, comment="图文描述"),
            "cover_image_url": fields.String(required=True, comment="首页图片"),
        },
        location="json",
    )
    def post(self, request, args):
        group_id = args.get("group_id")
        product_group = get_product_group_by_shop_id_and_id(self.current_shop.id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        serializer = ProductCreateSerializer(data=args, context={'self':self})
        if not serializer.is_valid():
            return self.send_error(
                error_message=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "product_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="货品ID"
            )
        },
        location="query"
    )
    def get(self, request, args):
        current_shop = self.current_shop
        product_id = args.get("product_id")
        product = get_product_with_group_name(current_shop.id, product_id)
        if not product:
            return self.send_fail(error_text="货品不存在")
        serializer = AdminProductSerializer(product)
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "name": fields.String(
                required=True, validate=[validate.Length(1, 15)], comment="货品名"
            ),
            "group_id": fields.Integer(required=True, comment="分组id"),
            "price": fields.Decimal(
                required=True,
                validate=[validate.Range(0, min_inclusive=False)],
                comment="货品单价",
            ),
            "code": fields.String(required=False, comment="货品编码"),
            "storage": fields.Decimal(
                required=True, validate=[validate.Range(0)], comment="库存"
            ),
            "summary": fields.String(
                required=False, validate=[validate.Length(0, 20)], comment="货品简介"
            ),
            "pictures": fields.List(
                fields.String(),
                required=False,
                validate=[validate.Length(1, 5)],
                comment="轮播图",
            ),
            "description": fields.String(required=False, comment="图文描述"),
            "cover_image_url": fields.String(required=False, comment="首页图片"),
            "product_id": fields.Integer(required=True, comment="货品ID"),
        },
        location="json",
    )
    def put(self, request, args):
        shop_id = self.current_shop.id
        product_id = args.pop("product_id")
        product = get_product_by_id(shop_id, product_id)
        if not product:
            return self.send_fail(error_text="货品不存在")
        group_id = args.pop("group_id")
        product_group = get_product_group_by_shop_id_and_id(shop_id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        serializer = AdminProductSerializer(product, data=request.data, context={"self":self})
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return self.send_success(data=serializer.data)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "product_ids": fields.List(
                fields.Integer(required=True),
                required=True,
                validate=[validate.Length(1)],
                commet="货品ID列表",
            )
        },
        location="json"
    )
    def delete(self, request, args):
        product_ids = args.get("product_ids")
        ret, info = delete_product_by_ids_and_shop_id(product_ids, self.current_shop.id)
        if not ret:
            return self.send_fail(error_text=info)
        else:
            return self.send_success()


class AdminProductsView(AdminBaseView):
    """后台-货品-获取货品列表&批量修改货品(上架，下架)"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "keyword": fields.String(required=False, missing="", comment="货品关键字"),
            "group_id": fields.Integer(required=True, comment="分组ID"),
            "status": StrToList(
                required=False,
                missing=[ProductStatus.ON, ProductStatus.OFF],
                validate=[validate.ContainsOnly([ProductStatus.ON, ProductStatus.OFF])],
                comment="货品状态,上架、下架",
            )
        },
        location="query"
    )
    def get(self, request, args):
        shop = self.current_shop
        product_list = list_product_by_filter(shop.id, **args)
        product_list = self._get_paginated_data(product_list, AdminProductSerializer)
        return self.send_success(data_list=product_list)

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "product_ids": fields.List(
                fields.Integer(required=True),
                required=True,
                validate=[validate.Length(1)],
                commet="货品ID列表",
            ),
            "operation_type": fields.Integer(
                required=False,
                missing=1,
                validate=[validate.OneOf(
                    [ProductOperationType.ON, ProductOperationType.OFF]
                )],
                comment="操作类型，1:上架，2：下架"
            )
        },
        location="json"
    )
    def put(self, request, args):
        operation_type = args.get("operation_type")
        product_ids = args.get("product_ids")
        product_list = list_product_by_ids(self.current_shop.id, product_ids)
        update_products_status(product_list, operation_type)
        return self.send_success()


class AdminProductGroupsView(AdminBaseView):
    """后台-货品-批量更新货品分组"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "product_ids": fields.List(
                fields.Integer(required=True),
                required=True,
                validate=[validate.Length(1)],
                comment="货品ID列表",
            ),
            "group_id": fields.Integer(required=True, comment="货品分组ID"),
        },
        location="json"
    )
    def put(self, request, args):
        shop = self.current_shop
        group_id = args.get("group_id")
        product_ids = args.pop("product_ids")
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
    @use_args(
        {
            "name": fields.String(
                required=True, validate=[validate.Length(1, 10)], comment="分组名"
            ),
            "description": fields.String(
                required=False, validate=[validate.Length(0, 50)], comment="分组描述"
            ),
        },
        location="json",
    )
    def post(self, request, args):
        serializer = AdminProductGroupSerializer(data=args, context={"self":self})
        if not serializer.is_valid():
            return self.send_error(status_code=status.HTTP_400_BAD_REQUEST, error_message=serializer.errors)
        serializer.save()
        return self.send_success(data=serializer.data)

    @use_args(
        {
            "name": fields.String(
                required=True, validate=[validate.Length(1, 10)], comment="分组名"
            ),
            "description": fields.String(
                required=False, validate=[validate.Length(0, 50)], comment="分组描述"
            ),
            "group_id": fields.Integer(required=True, comment="分组ID"),
        },
        location="json"
    )
    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    def put(self, request, args):
        group_id = args.pop("group_id")
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
    @use_args(
        {"group_id": fields.Integer(required=True, comment="分组ID")}, location="json"
    )
    def delete(self, request, args):
        shop = self.current_shop
        group_id = args.get("group_id")
        product_group = get_product_group_by_shop_id_and_id(shop.id, group_id)
        if not product_group:
            return self.send_fail(error_text="货品分组不存在")
        ret, info = delete_product_group_by_id_and_shop_id(product_group, group_id, shop.id)
        if not ret:
            return self.send_fail(error_text=info)
        else:
            return self.send_success()

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "status": StrToList(
                required=False,
                missing=[ProductStatus.ON, ProductStatus.OFF],
                validate=[
                    validate.ContainsOnly(
                        [ProductStatus.ON, ProductStatus.OFF]
                    )
                ],
                comment="货品状态,上架/下架",
            )
        },
        location="query"
    )
    def get(self, request, args):
        shop = self.current_shop
        product_group_with_count = list_product_group_with_product_count(shop.id, **args)
        serializer = AdminProductGroupSerializer(product_group_with_count, many=True)
        return self.send_success(data_list=serializer.data)


class AdminProductGroupSortView(AdminBaseView):
    """后台-货品-分组排序"""

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "group_ids": fields.List(
                fields.Integer(required=True),
                required=True,
                validate=[validate.Length(1)],
                comment="货品分组ID列表",
            )
        },
        location="json"
    )
    def put(self, request, args):
        group_ids = args.get("group_ids")
        shop = self.current_shop
        sort_shop_product_group(shop.id, group_ids)
        return self.send_success()


class AdminProductSaleRecordView(AdminBaseView):
    """后台-货品-货品详情-获取货品销售记录"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required([AdminBaseView.staff_permissions.ADMIN_PRODUCT])
    @use_args(
        {
            "product_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="货品ID"
            )
        },
        location="query"
    )
    def get(self, request, args):
        product_id = args.get("product_id")
        shop = self.current_shop
        product_sale_record_list = list_order_with_order_lines_by_product_id_interface(shop.id, product_id)
        product_sale_record_list = self._get_paginated_data(
            product_sale_record_list, AdminProductSaleRecordSerializer
        )
        return self.send_success(data_list=product_sale_record_list)


class MallProductView(MallBaseView):
    """商城-货品-获取单个货品详情"""

    @use_args({"product_id": fields.Integer(required=True, comment="货品ID")}, location="query")
    def get(self, request, args, shop_code):
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        product_id = args.get("product_id")
        product = get_product_with_group_name(shop.id, product_id)
        serializer = MallProductSerializer(product)
        return self.send_success(data=serializer.data)


class MallProductsView(MallBaseView):
    """商城-货品-获取所有分组及旗下货品"""

    def get(self, request, shop_code):
        self._set_current_shop(request, shop_code)
        shop = self.current_shop
        product_group_list = list_product_group_with_product_list(shop.id)
        serializer = MallProductGroupSerializer(product_group_list, many=True)
        return self.send_success(data_list=serializer.data)

