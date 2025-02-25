from django.shortcuts import render
from django.conf import settings
import os
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

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

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_dataset(self, request):
        print("请求方法:", request.method)  # 调试日志
        print("请求内容类型:", request.content_type)  # 调试内容类型
        print("Received files:", request.FILES)  # 调试日志
        print("Received data:", request.data)    # 调试日志
        print("Files keys:", request.FILES.keys())  # 更多调试信息
        print("Data keys:", request.data.keys() if hasattr(request.data, 'keys') else "无keys方法")    # 更多调试信息

        # 文件可能在FILES或DATA中
        found_file = None
        
        # 检查FILES
        if 'data' in request.FILES:
            found_file = request.FILES['data']
        elif request.FILES:
            # 使用第一个可用文件
            found_file = request.FILES[next(iter(request.FILES))]
            
        # 检查DATA中的文件
        if not found_file and 'data' in request.data:
            try:
                # 可能是InMemoryUploadedFile对象
                found_file = request.data['data']
            except:
                print("从data字典获取文件失败")
        
        if not found_file:
            return Response({
                "error": "未找到上传的文件",
                "content_type": request.content_type,
                "received_data": str(request.data),
                "received_files": str(request.FILES)
            }, status=status.HTTP_400_BAD_REQUEST)

        dataset_file = found_file
        dataset_dir = os.path.join(settings.MEDIA_ROOT, "datasets")
        
        # 确保目录存在
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
            
        file_path = os.path.join(dataset_dir, dataset_file.name)
        
        try:
            with open(file_path, 'wb+') as dest:
                for chunk in dataset_file.chunks():
                    dest.write(chunk)
            
            return Response({
                "message": "数据集上传成功",
                "filename": dataset_file.name
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": f"文件上传失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
