from data_manager.models import DatasetManagerModel
from dvadmin.utils.serializers import CustomModelSerializer


class DatasetManagerSerializer(CustomModelSerializer):
    """
    数据集管理-序列化器
    """

    class Meta:
        model = DatasetManagerModel
        fields = "__all__"
        read_only_fields = ["id"]

class DatasetManagerCreateUpdateSerializer(CustomModelSerializer):
    """
    数据集管理 创建/更新时的列化器
    """

    class Meta:
        model = DatasetManagerModel
        fields = "__all__"
        read_only_fields = ["id"]