"""测试使用"""
from urllib.parse import urlencode

from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from celery_tasks.celery_autowork_task import auto_cancel_order
from celery_tasks.celery_tplmsg_task import OrderCommitTplMsg
from demo.serializers import DemoSerializer
from shop.models import HistoryRealName, Shop
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
        user_id = request.query_params.get("user_id")
        user = User.objects.filter(id=user_id).first()
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return self.send_success(token=token)

    def post(self, request):
        res = auto_cancel_order.apply_async(args=[1,1], countdown=15 * 60)
        print(res)
        return Response()