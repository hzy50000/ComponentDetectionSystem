Model层(POJO):

- 位于 dvadmin/system/models.py
- 核心模型:
  - Users - 用户模型
  - Role - 角色模型
  - Dept - 部门模型
  - Menu - 菜单模型
  - SystemConfig - 系统配置
  - Dictionary - 数据字典
  - OperationLog - 操作日志

Controller层:

- 位于 dvadmin/system/views/ 目录
- 使用Django REST framework的ViewSet
- 主要控制器:
  - UserViewSet - 用户管理
  - RoleViewSet - 角色管理
  - MenuViewSet - 菜单管理
  - DeptViewSet - 部门管理

URL映射:

- 位于 dvadmin/system/urls.py
- 使用REST framework的路由系统
- API路径映射:
  - /menu/ -> MenuViewSet
  - /role/ -> RoleViewSet
  - /user/ -> UserViewSet
  - /dept/ -> DeptViewSet

---

1. 预测API端点：`/api/unet/predict/`
2. 请求方式：POST
3. 请求参数：
   - image: 图片文件（必需）
   - scale_factor: 缩放因子（可选，默认1.0）
   - threshold: 预测阈值（可选，默认0.5）
4. 返回格式：

```json
{
    "message": "预测成功",
    "result_url": "预测结果图片的URL"
}
```

API集成了以下功能：

- 自动模型加载和设备选择（CPU/GPU）
- 图像预处理和后处理
- 结果图片保存和URL生成
- 错误处理和日志记录