"""测试使用"""
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from demo.serializers import DemoSerializer
from shop.models import HistoryRealName
from user.models import User
from wsc_django.utils.views import GlobalBaseView, UserBaseView


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
        user = User.objects.filter(id=1).first()
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return self.send_success(token=token)

    def post(self, request):
        return Response()