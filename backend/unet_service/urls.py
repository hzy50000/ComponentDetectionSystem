from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UNetViewSet

# 创建路由器并注册视图
router = DefaultRouter()
router.register(r'', UNetViewSet, basename='unet')

urlpatterns = [
    path('', include(router.urls)),
]