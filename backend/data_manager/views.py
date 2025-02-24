from django.shortcuts import render

from data_manager.models import DatasetManagerModel
from data_manager.serializers import DatasetManagerSerializer, DatasetManagerCreateUpdateSerializer
from dvadmin.utils.viewset import CustomModelViewSet


class DatasetModelViewSet(CustomModelViewSet):
    """
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = DatasetManagerModel.objects.all()
    serializer_class = DatasetManagerSerializer
    create_serializer_class = DatasetManagerCreateUpdateSerializer
    update_serializer_class = DatasetManagerCreateUpdateSerializer
    filter_fields = ['name', 'type']
    search_fields = ['name']
