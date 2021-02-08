from django.utils.deprecation import MiddlewareMixin

from user.models import User


class MyMiddleware(MiddlewareMixin):
    """测试使用，免去登录"""

    def process_request(self, request):
        user = User.objects.get(id=1)
        request.user = user