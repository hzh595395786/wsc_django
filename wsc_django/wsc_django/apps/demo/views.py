"""测试使用"""
from rest_framework.pagination import PageNumberPagination
from rest_framework_jwt.settings import api_settings

from demo.serializers import DemoSerializer
from user.models import User
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
        from wsc_django.utils.authenticate import SimpleEncrypt
        import time
        timestamp = int(time.time())
        id = 1
        text = '%d@%d'%(timestamp, id)
        res = SimpleEncrypt.encrypt(text)
        return self.send_success(data=res)

