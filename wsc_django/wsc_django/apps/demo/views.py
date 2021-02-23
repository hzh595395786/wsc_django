"""测试使用"""
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from wsc_django.utils.authenticate import WSCIsLoginAuthenticate
from wsc_django.utils.views import UserBaseView
from demo.serializers import DemoSerializer


class DemoView(UserBaseView):
    """测试使用"""

    # permission_classes = [WSCAdminPermission]
    authentication_classes = (WSCIsLoginAuthenticate,)
    # serializer_class = DemoSerializer

    def get(self, request):

        return self.send_success()

    def post(self, request):
        return Response()