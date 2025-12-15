from django.db import models
from django.contrib.auth.models import User

class AiInteraction(models.Model):
    # 定义意图选项，方便管理和查询
    class Intent(models.TextChoices):
        CUSTOMER_CREATE = 'customer.create', '创建客户'
        CUSTOMER_LIST = 'customer.list', '查看客户'
        TALK = 'talk', '闲聊'
        UNKNOWN = 'unknown', '未知意图'
        ERROR = 'error', '处理错误'

    # 基础信息
    id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(
        User,
        related_name='ai_interactions',
        on_delete=models.CASCADE,
        verbose_name="所属用户"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    # 用户输入与上下文
    user_input = models.TextField(verbose_name="用户原始输入")
    context = models.JSONField(blank=True, null=True, verbose_name="请求上下文")

    # 意图识别结果 (LLM输出)
    intent = models.CharField(
        max_length=50,
        choices=Intent.choices,
        blank=True,
        null=True,
        verbose_name="识别出的意图"
    )
    slots = models.JSONField(blank=True, null=True, verbose_name="提取出的槽位")

    # 指令生成结果 (后端输出)
    generated_command = models.JSONField(blank=True, null=True, verbose_name="生成的指令")

    def __str__(self):
        return f"{self.owner.username} - {self.user_input[:30]}..."

    class Meta:
        verbose_name = "AI 交互日志"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']