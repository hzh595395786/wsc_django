from rest_framework import status
from rest_framework.response import Response

from customer.services import get_customer_by_customer_id_and_shop_id
from wsc_django.utils.views import AdminBaseView
from customer.serializers import AdminCustomerSerializer


class AdminCustomerView(AdminBaseView):
    """后台-客户-客户详情"""

    @AdminBaseView.permission_required(
        [AdminBaseView.staff_permissions.ADMIN_CUSTOMER]
    )
    def get(self, request):
        customer_id = request.query_params.get("customer_id", None)
        if not customer_id:
            return self.send_error(
                error_message={"message":"缺少customer_id"}, status_code=status.HTTP_400_BAD_REQUEST
            )
        customer = get_customer_by_customer_id_and_shop_id(
            customer_id,
            self.current_shop.id,
            with_user_info=True,
        )
        if customer:
            serializer = AdminCustomerSerializer(customer)
            return self.send_success(data=serializer.data)
        else:
            return self.send_fail(error_text="客户不存在")
