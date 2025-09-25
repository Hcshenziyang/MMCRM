from rest_framework import serializers
from .models import ProjectStage, Project, Activity


# 项目管理
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'owner', 'current_stage',
                  'source', 'description', 'expected_revenue', 'expected_close_date',
                   'actual_revenue', 'actual_close_date', 'created_at', 'updated_at']


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'project', 'activity_type', 'description',
                  'activity_date', 'created_by', 'created_at', 'updated_at']
