from django.db import models

from dvadmin.utils.models import CoreModel


# 数据集管理类
class DatasetManagerModel(CoreModel):
    """
    数据集管理
    """
    id = models.BigAutoField(primary_key=True,verbose_name="数据集Id")
    name = models.CharField(max_length=50, verbose_name="数据集名称", unique=True)
    description = models.TextField(verbose_name="数据集描述", blank=True, null=True)
    data = models.BinaryField(verbose_name="数据集文件", blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="数据集创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="数据集更新时间")
    owner_id = models.IntegerField(verbose_name="数据集拥有者id", blank=True, null=True)
    type = models.CharField(max_length=50, verbose_name="数据集类型", blank=True, null=True)


    class Meta:
        db_table = "dataset_manager"
        verbose_name = "数据集管理"
        verbose_name_plural = verbose_name