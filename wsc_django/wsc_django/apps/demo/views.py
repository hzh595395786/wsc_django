"""测试使用"""
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from django_redis import get_redis_connection

from staff.services import get_staff_by_user_id_and_shop_id
from wsc_django.utils.permission import WSCAdminPermission
from demo.serializers import DemoSerializer


class DemoView(GenericAPIView):
    """测试使用"""

    permission_classes = [WSCAdminPermission]
    serializer_class = DemoSerializer

    def get(self, request):
        serializer = DemoSerializer()
        # redis_conn = get_redis_connection('verify_codes')
        # pl = redis_conn.pipeline()
        # pl.setex('test', 60, 1)
        # pl.execute()
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        shop = request.shop
        staff = get_staff_by_user_id_and_shop_id(user.id, shop.id)
        return Response()