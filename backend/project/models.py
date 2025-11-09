from django.db import models
from django.conf import settings  # 导入settings以获取AUTH_USER_MODEL
from customer.models import Customer  # 假设你的客户模型在customer app中


class ProjectStage(models.Model):
    """
    项目阶段模型，例如：销售、成交、售后、完结
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="阶段名称")
    order = models.PositiveSmallIntegerField(unique=True, verbose_name="排序")
    description = models.TextField(blank=True, verbose_name="阶段描述")  # 可以增加描述字段

    def __str__(self):
        return self.name


class Project(models.Model):
    """
    项目模型，用于记录销售过程中的各个项目。
    """

    # 线索来源选项
    SOURCE_CHOICES = [
        ('website', '官网咨询'),
        ('phone_call', '电话拜访'),
        ('referral', '客户推荐'),
        ('sales_assignment', '销售主管分配'),
        ('self_generated', '自行开发'),
        ('other', '其他'),
    ]

    name = models.CharField(max_length=200, verbose_name="项目名称")
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,  # 客户删除时，项目也删除
        related_name='projects',
        verbose_name="关联客户"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # 使用settings.AUTH_USER_MODEL引用用户模型
        on_delete=models.SET_NULL,  # 用户删除时，项目负责人设为NULL，保留项目记录
        related_name='owned_projects',
        blank=True,  # 允许没有负责人
        null=True,  # 数据库中允许NULL
        verbose_name="项目负责人"
    )
    current_stage = models.ForeignKey(
        ProjectStage,
        on_delete=models.PROTECT,  # 阶段被删除时，阻止删除，直到没有项目关联此阶段
        related_name='projects_in_stage',
        verbose_name="当前阶段"
    )
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='self_generated',
        verbose_name="项目线索来源"
    )
    description = models.TextField(blank=True, verbose_name="项目描述")
    revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="销售额"
    )
    close_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="成交日期"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return self.name

    # 用于判断项目是否已成交
    def is_closed(self):
        return self.current_stage.name in ['成交', '售后', '完结']


class Activity(models.Model):
    """
    记录销售人员在每个项目上的具体行动。
    """

    ACTIVITY_TYPE_CHOICES = [
        ('call', '电话'),
        ('visit', '拜访'),
        ('email', '邮件'),
        ('meeting', '会议'),
        ('demo', '产品演示'),
        ('proposal', '提交方案'),
        ('other', '其他'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,  # 项目删除时，所有相关行动记录也删除
        related_name='activities',
        verbose_name="关联项目"
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPE_CHOICES,
        default='call',
        verbose_name="行动类型"
    )
    description = models.TextField(verbose_name="行动详情")
    activity_date = models.DateTimeField(verbose_name="行动日期") # 可以是DateTimeField，记录具体时间
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # 创建人删除时，保留行动记录，创建人设为NULL
        related_name='created_activities',
        blank=True,
        null=True,
        verbose_name="创建人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "行动记录"
        verbose_name_plural = "行动记录"
        ordering = ['-activity_date'] # 按行动日期倒序排列

    def __str__(self):
        return f"{self.project.name} - {self.get_activity_type_display()} on {self.activity_date.strftime('%Y-%m-%d')}"