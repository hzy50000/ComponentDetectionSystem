import io
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .unet_predictor import UNetPredictor


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

    @action(detail=False, methods=['POST'])
    def predict(self, request):
        """
        处理图片预测请求
        """
        try:
            # 检查是否有文件上传
            if 'image' not in request.FILES:
                return Response(
                    {'error': '没有上传图片'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            image_file = request.FILES['image']
            
            # 获取缩放因子和阈值参数（可选）
            scale_factor = float(request.data.get('scale_factor', 1.0))
            threshold = float(request.data.get('threshold', 0.5))

            # 获取预测器实例
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

            # 保存结果图片到临时目录
            temp_path = default_storage.save(
                f'temp/predict_{Path(image_file.name).stem}_result.png',
                ContentFile(img_byte_arr)
            )
            
            # 构建完整的URL
            result_url = request.build_absolute_uri(default_storage.url(temp_path))

            return Response({
                'message': '预测成功',
                'result_url': result_url
            })

        except Exception as e:
            return Response(
                {'error': f'预测过程发生错误: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
