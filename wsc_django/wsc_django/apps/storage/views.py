from webargs import fields, validate
from webargs.djangoparser import use_args

from storage.serializers import AdminProductStorageRecordsSerializer
from storage.services import list_product_storage_record_by_product_id
from wsc_django.utils.pagination import StandardResultsSetPagination
from wsc_django.utils.views import AdminBaseView


class AdminProductStorageRecordsView(AdminBaseView):
    """后台-货品-货品库存变更"""
    pagination_class = StandardResultsSetPagination

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_PRODUCT]
    )
    @use_args(
        {
            "product_id": fields.Integer(
                required=True, validate=[validate.Range(1)], comment="货品ID"
            ),
        },
        location="query"
    )
    def get(self, request, args):
        shop_id = self.current_shop.id
        product_storage_record_list = list_product_storage_record_by_product_id(
            shop_id, **args
        )
        product_storage_record_list = self._get_paginated_data(
            product_storage_record_list, AdminProductStorageRecordsSerializer
        )
        return self.send_success(data_list=product_storage_record_list)
