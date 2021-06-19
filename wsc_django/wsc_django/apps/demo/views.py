"""测试使用"""
from django_redis import get_redis_connection
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from delivery.models import DeliveryConfig
from demo.serializers import DemoSerializer
from product.services import create_product_pictures
from shop.utils import put_qcode_file_to_tencent_cos, get_shop_mini_program_qcode
from user.models import User
from user.services import get_user_by_id
from wsc_django.utils.views import GlobalBaseView


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 20

class DemoView(GlobalBaseView):
    """测试使用"""

    # permission_classes = [WSCAdminPermission]
    # authentication_classes = (WSCIsLoginAuthenticate,)
    serializer_class = DemoSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        user_id = request.query_params.get("user_id")
        user = User.objects.filter(id=user_id).first()
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        import datetime
        payload = jwt_payload_handler(user, datetime.timedelta(days=1))
        token = jwt_encode_handler(payload)
        return self.send_success(token=token)

    def post(self, request):
        qcode_file = get_shop_mini_program_qcode('bc7712bac')
        response = put_qcode_file_to_tencent_cos(qcode_file, 'bc7712bac')
        return self.send_success(data=response)