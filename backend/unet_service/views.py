import io
import zipfile
from pathlib import Path
import tempfile
import os
import logging
import imghdr

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from PIL import Image

from .unet_predictor import UNetPredictor

logger = logging.getLogger(__name__)

class UNetViewSet(viewsets.ViewSet):
    """
    UNet模型预测服务的视图集
    """
    permission_classes = [AllowAny]  # 允许所有用户访问
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.predictor = None

    def get_predictor(self):
        """
        懒加载预测器实例
        """
        if self.predictor is None:
            self.predictor = UNetPredictor()
        return self.predictor

    def _process_single_image(self, image_file, scale_factor, threshold, request):
        """
        处理单张图片并返回结果URL
        """
        try:
            predictor = self.get_predictor()
            
            # 预测
            mask_image = predictor.predict(
                image_file,
                scale_factor=scale_factor,
                out_threshold=threshold
            )

            # 将预测结果转换为字节流
            img_byte_arr = io.BytesIO()
            mask_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            # 生成唯一的文件名
            timestamp = Path(image_file.name).stem
            temp_path = default_storage.save(
                f'temp/predict_{timestamp}_{os.urandom(4).hex()}_result.png',
                ContentFile(img_byte_arr)
            )
            
            # 构建完整的URL
            result_url = request.build_absolute_uri(default_storage.url(temp_path))
            logger.info(f"Generated result URL: {result_url}")
            return result_url
        except Exception as e:
            logger.error(f"Error processing image {image_file.name}: {str(e)}")
            raise

    def _is_valid_image(self, file_path):
        """
        检查文件是否为有效的图片
        """
        try:
            # 首先使用imghdr检查文件类型
            img_type = imghdr.what(file_path)
            if img_type not in ['jpeg', 'png', 'bmp']:
                return False

            # 尝试打开和读取图片
            with Image.open(file_path) as img:
                img.load()  # 这会验证图片数据是否完整
            return True
        except Exception as e:
            logger.warning(f"Invalid image file {file_path}: {str(e)}")
            return False

    @action(detail=False, methods=['POST'])
    def predict(self, request):
        """
        处理图片预测请求，支持单张图片或ZIP文件
        """
        try:
            # 检查是否有文件上传或数据集路径
            uploaded_file = None
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
            elif 'data' in request.data:
                dataset_path = request.data['data']
                # 确保路径是相对于media目录的
                full_path = os.path.join(settings.MEDIA_ROOT, dataset_path)
                if os.path.exists(full_path):
                    # 创建 File 对象
                    with open(full_path, 'rb') as f:
                        content = f.read()
                        uploaded_file = ContentFile(content, name=os.path.basename(full_path))
                else:
                    return Response(
                        {'error': f'找不到数据集文件: {dataset_path}'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            if not uploaded_file:
                return Response(
                    {'error': '没有上传文件或提供有效的数据集路径'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            logger.info(f"Received file: {uploaded_file.name}")
            
            # 获取缩放因子和阈值参数（可选）
            scale_factor = float(request.data.get('scale_factor', 1.0))
            threshold = float(request.data.get('threshold', 0.5))

            # 检查是否为ZIP文件
            if uploaded_file.name.lower().endswith('.zip'):
                logger.info("Processing ZIP file")
                result_urls = []
                processed_files = 0
                failed_files = 0
                
                # 创建临时目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    logger.info(f"Created temp directory: {temp_dir}")
                    
                    # 保存ZIP文件
                    zip_path = os.path.join(temp_dir, 'upload.zip')
                    with open(zip_path, 'wb') as f:
                        for chunk in uploaded_file.chunks():
                            f.write(chunk)
                    
                    try:
                        # 解压ZIP文件
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            # 获取所有文件列表
                            file_list = [f for f in zip_ref.namelist() if not f.startswith('__MACOSX/')]
                            logger.info(f"Files in ZIP: {file_list}")
                            
                            zip_ref.extractall(temp_dir)
                            logger.info(f"Extracted ZIP file to {temp_dir}")
                    except Exception as e:
                        logger.error(f"Error extracting ZIP file: {str(e)}")
                        return Response(
                            {'error': f'ZIP文件解压失败: {str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # 处理所有图片
                    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            file_ext = os.path.splitext(file)[1].lower()
                            
                            # 跳过__MACOSX目录和其他非图片文件
                            if '__MACOSX' in file_path or file_ext not in image_extensions:
                                logger.info(f"Skipping non-image file: {file_path}")
                                continue
                                
                            logger.info(f"Processing file: {file_path}")
                            
                            # 验证是否为有效图片
                            if not self._is_valid_image(file_path):
                                logger.warning(f"Invalid image file: {file_path}")
                                failed_files += 1
                                continue

                            try:
                                # 读取图片文件
                                with open(file_path, 'rb') as img_file:
                                    img_content = img_file.read()
                                    
                                # 创建Django文件对象
                                django_file = ContentFile(img_content)
                                django_file.name = os.path.basename(file_path)
                                
                                # 处理单张图片
                                result_url = self._process_single_image(
                                    django_file,
                                    scale_factor,
                                    threshold,
                                    request
                                )
                                logger.info(f"Successfully processed {file_path}")
                                result_urls.append(result_url)
                                processed_files += 1
                            except Exception as e:
                                logger.error(f"Error processing {file_path}: {str(e)}")
                                failed_files += 1
                                continue

                logger.info(f"ZIP processing complete. Processed: {processed_files}, Failed: {failed_files}")
                
                if not result_urls:
                    return Response(
                        {'error': 'ZIP文件中没有有效的图片文件或处理过程中出错'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response({
                    'message': f'预测成功，成功处理{processed_files}个文件，失败{failed_files}个文件',
                    'result_urls': result_urls
                })
            else:
                # 处理单张图片
                logger.info("Processing single image")
                result_url = self._process_single_image(
                    uploaded_file,
                    scale_factor,
                    threshold,
                    request
                )
                
                return Response({
                    'message': '预测成功',
                    'result_url': result_url
                })

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return Response(
                {'error': f'预测过程发生错误: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
