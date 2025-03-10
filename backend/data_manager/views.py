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
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']  # 明确指定允许的HTTP方法

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

        # 处理found_file
        if isinstance(found_file, str):
            # 如果是字符串路径，尝试多个可能的路径
            possible_paths = [
                os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, found_file),  # 完整路径
                os.path.join(settings.BASE_DIR, found_file),  # 相对于BASE_DIR的路径
                found_file,  # 原始路径
            ]
            
            print("尝试查找文件路径...")
            for try_path in possible_paths:
                print(f"尝试路径: {try_path}")
                if os.path.exists(try_path):
                    print(f"找到文件: {try_path}")
                    file_path = try_path
                    break
            else:
                return Response({
                    "error": f"找不到文件: {found_file}",
                    "tried_paths": possible_paths
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 获取文件名
            file_name = os.path.basename(found_file)
            dataset_file = found_file
        else:
            if not hasattr(found_file, 'name'):
                return Response({
                    "error": "文件对象缺少name属性",
                    "received_type": str(type(found_file))
                }, status=status.HTTP_400_BAD_REQUEST)
            dataset_file = found_file
            file_name = dataset_file.name

        # 创建目标目录
        dataset_dir = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT, "datasets")
        
        # 确保目录存在
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
            
        target_path = os.path.join(dataset_dir, file_name)
        print("目标目录:", dataset_dir)  # 调试日志
        
        try:
            if isinstance(dataset_file, str):
                # 如果是字符串路径，直接复制文件
                import shutil
                source_path = file_path  # 使用之前找到的有效文件路径
                print("复制文件 - 源路径:", source_path)  # 调试日志
                print("复制文件 - 目标路径:", target_path)  # 调试日志
                shutil.copy2(source_path, target_path)
            else:
                # 如果是文件对象，按块写入
                with open(target_path, 'wb+') as dest:
                    for chunk in dataset_file.chunks():
                        dest.write(chunk)
            
            # 创建数据集记录
            relative_path = os.path.join('datasets', file_name)  # 存储相对路径
            
            # 从请求中获取数据集信息
            dataset_data = {
                'name': request.data.get('name', ''),  # 必须提供名称
                'description': request.data.get('description', ''),
                'type': request.data.get('type', ''),
                'data': relative_path,  # 存储相对路径
                'owner_id': request.user.id if request.user.is_authenticated else None
            }

            # 如果没有提供名称，则使用文件名（不包含扩展名）
            if not dataset_data['name']:
                dataset_data['name'] = os.path.splitext(file_name)[0]

            print("要创建的数据集记录:", dataset_data)  # 调试日志

            # 使用序列化器创建数据集记录
            serializer = DatasetManagerCreateUpdateSerializer(data=dataset_data)
            if serializer.is_valid():
                try:
                    dataset = serializer.save()
                    return Response({
                        "message": "数据集上传成功",
                        "id": dataset.id,
                        "name": dataset.name,
                        "data": serializer.data
                    }, status=status.HTTP_200_OK)
                except Exception as e:
                    # 如果保存失败，删除已上传的文件
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    return Response({
                        "error": f"创建数据集记录失败: {str(e)}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # 如果验证失败，删除已上传的文件
                if os.path.exists(target_path):
                    os.remove(target_path)
                return Response({
                    "error": "数据集信息验证失败",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "error": f"文件上传失败: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
