from rest_framework.routers import SimpleRouter

from data_manager.views import DatasetModelViewSet

router = SimpleRouter()
router.register("api/datasetManager", DatasetModelViewSet)

urlpatterns = [
]
urlpatterns += router.urls