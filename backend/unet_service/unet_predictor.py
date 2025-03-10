import os
import sys
import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
from pathlib import Path

# 添加Pytorch-UNet目录到Python路径
current_dir = Path(__file__).resolve().parent
pytorch_unet_path = str(current_dir / 'Pytorch-UNet')
if pytorch_unet_path not in sys.path:
    sys.path.append(pytorch_unet_path)

# 导入UNet相关模块
from unet import UNet
from utils.data_loading import BasicDataset

class UNetPredictor:
    def __init__(self, model_path=None, device=None):
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
            
        self.net = UNet(n_channels=3, n_classes=2, bilinear=False)
        self.net.to(device=self.device)
        
        if model_path is None:
            # 默认模型路径
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_path = str(base_dir / 'Pytorch-UNet' / 'checkpoints' / 'MODEL.pth')
            
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        # 加载模型
        state_dict = torch.load(model_path, map_location=self.device)
        self.mask_values = state_dict.pop('mask_values', [0, 1])
        self.net.load_state_dict(state_dict)
        self.net.eval()

    def predict(self, image_file, scale_factor=1, out_threshold=0.5):
        """
        对输入图片进行预测
        
        Args:
            image_file: 图片文件对象或路径
            scale_factor: 图片缩放因子
            out_threshold: 输出阈值
            
        Returns:
            预测结果图片对象
        """
        # 如果输入是文件对象，直接打开；如果是路径字符串，用PIL打开
        if isinstance(image_file, (str, Path)):
            img = Image.open(image_file)
        else:
            img = Image.open(image_file)
            
        # 预处理图片
        img_data = torch.from_numpy(BasicDataset.preprocess(None, img, scale_factor, is_mask=False))
        img_data = img_data.unsqueeze(0)
        img_data = img_data.to(device=self.device, dtype=torch.float32)
        
        # 预测
        with torch.no_grad():
            output = self.net(img_data).cpu()
            output = F.interpolate(output, (img.size[1], img.size[0]), mode='bilinear')
            if self.net.n_classes > 1:
                mask = output.argmax(dim=1)
            else:
                mask = torch.sigmoid(output) > out_threshold
                
        # 获取预测掩码
        mask = mask[0].long().squeeze().numpy()
        
        # 转换为图片
        return self._mask_to_image(mask)
    
    def _mask_to_image(self, mask):
        """
        将预测掩码转换为图片
        """
        if isinstance(self.mask_values[0], list):
            out = np.zeros((mask.shape[-2], mask.shape[-1], len(self.mask_values[0])), dtype=np.uint8)
        elif self.mask_values == [0, 1]:
            out = np.zeros((mask.shape[-2], mask.shape[-1]), dtype=bool)
        else:
            out = np.zeros((mask.shape[-2], mask.shape[-1]), dtype=np.uint8)

        if mask.ndim == 3:
            mask = np.argmax(mask, axis=0)

        for i, v in enumerate(self.mask_values):
            out[mask == i] = v

        return Image.fromarray(out)