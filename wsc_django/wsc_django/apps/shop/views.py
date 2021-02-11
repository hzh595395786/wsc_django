from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shop.models import Shop
from wsc_django.utils.authenticate import WSCAuthenticate
from wsc_django.utils.setup import get_format_response_data
from shop.serializers import ShopCreateSerializer, ShopDetailSerializer
from shop.services import (
    get_shop_by_shop_id
)


class ShopView(APIView):
    """商城端-商铺创建&商铺详情"""
    # authentication_classes = [WSCAuthenticate]

    def post(self, request):
        serializer = ShopCreateSerializer(data=request.data, context={'request':request})
        if not serializer.is_valid():
            return Response({'message':"缺少参数或参数有误"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        data = get_format_response_data(serializer.data, True)
        return Response(data=data)

    def get(self, request):
        shop_id = request.query_params.get("shop_id", None)
        if not shop_id:
            return Response({'message':"缺少参数或参数有误"}, status=status.HTTP_400_BAD_REQUEST)
        shop = get_shop_by_shop_id(shop_id)
        if not shop:
            return Response({'message':"店铺不存在"}, status=status.HTTP_404_NOT_FOUND)
        shop = Shop.objects.get(id=shop_id)
        serializer = ShopDetailSerializer(shop)
        data = get_format_response_data(serializer.data, True)
        return Response(data=data)



