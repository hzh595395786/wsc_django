from django.urls import path
from ws import consumers

websocket_urlpatterns = [
    path('api/admin/websocket/', consumers.AdminWebSocketConsumer.as_asgi()),  # 后台的websocket
]