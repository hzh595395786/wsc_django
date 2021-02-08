from rest_framework.generics import CreateAPIView


# Create your views here.
from wsc_django.utils.verify import WSCPermission
from shop.serializers import ShopCreateSerializer


class ShopCreateView(CreateAPIView):
    """商城端-店铺创建"""
    # permission_classes = [WSCPermission]
    serializer_class = ShopCreateSerializer


