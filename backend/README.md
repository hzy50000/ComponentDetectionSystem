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