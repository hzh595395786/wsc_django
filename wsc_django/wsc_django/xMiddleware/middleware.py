from django.utils.deprecation import MiddlewareMixin

from user.models import User
from shop.services import (
    get_shop_by_shop_code,
    get_shop_by_shop_id,
)


class MyMiddleware(MiddlewareMixin):
    """测试使用，免去登录"""

    def process_request(self, request):
        user = User.objects.get(id=1)
        self.current_user = user


class ConfigMiddleware(MiddlewareMixin):
    """进行一些配置"""

    def process_request(self, request):
        # 从请求体中获取shop_code进行查询
        shop_code = request.GET.get("shop_code")
        shop = None
        if shop_code:
            shop = get_shop_by_shop_code(shop_code)
        wsc_shop_id = request.COOKIES.get("wsc_shop_id")
        # 从cookie中获取shop_id进行查询
        if wsc_shop_id and not shop:
            shop = get_shop_by_shop_id(int(wsc_shop_id))
        request.shop = shop