from rest_framework import serializers
from .models import ProjectStage, Project, Activity
from customer.models import Customer
from django.contrib.auth.models import User

class CustomerSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name']


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class ProjectStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectStage
        fields = ['id', 'name']


class ProjectSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name']

# 项目管理
class ProjectSerializer(serializers.ModelSerializer):
    customer = CustomerSimpleSerializer(read_only=True)
    owner = UserSimpleSerializer(read_only=True) # owner 保持只读
    current_stage = ProjectStageSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer'

    )
    current_stage_id = serializers.PrimaryKeyRelatedField(
        queryset=ProjectStage.objects.all(),
        source='current_stage'
    )

    class Meta:
        model = Project
        fields = [
            'id', 'name',
            'customer', 'owner', 'current_stage', # 用于读取（GET）的嵌套字段
            'customer_id', 'current_stage_id',    # 用于写入（POST/PATCH）的ID字段
            'source', 'description', 'revenue', 'close_date', 'created_at', 'updated_at'
        ]

class ActivitySerializer(serializers.ModelSerializer):
    project = ProjectSimpleSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project'
    )
    created_by = UserSimpleSerializer(read_only=True)  # owner 保持只读
    class Meta:
        model = Activity
        fields = ['id', 'project', 'project_id', 'activity_type', 'description',
                  'activity_date', 'created_by', 'created_at', 'updated_at']
