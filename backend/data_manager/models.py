from django.db import models

from dvadmin.utils.models import CoreModel


# 数据集管理类
class DatasetManagerModel(CoreModel):
    """
    数据集管理
    """
    id = models.BigAutoField(primary_key=True,verbose_name="数据集Id")
    name = models.CharField(max_length=50, verbose_name="数据集名称", unique=True)
    data = models.CharField(max_length=255, verbose_name="数据集文件路径", blank=True, null=True)
    type = models.CharField(max_length=50, verbose_name="数据集类型", blank=True, null=True)


    class Meta:
        db_table = "dataset_manager"
        verbose_name = "数据集管理"
        verbose_name_plural = verbose_name