from django.db import models
class BaseModel(models.Model):
    create_times=models.DateTimeField(auto_now_add=True,verbose_name='创建时间')
    update_times=models.DateTimeField(auto_now=True,verbose_name='更新时间')
    is_delete=models.BooleanField(default=True,verbose_name='删除标记')

    class Meta:
        abstract=True
        # 抽象模型类