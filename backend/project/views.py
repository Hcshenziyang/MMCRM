# project/views.py
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from mycrm.permissions import CachedModelPermissions
from .models import Project, Activity, ProjectStage
from .serializers import ProjectSerializer, ActivitySerializer, ProjectStageSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """
    项目视图集：支持增删改查、阶段流转、筛选、搜索
    """
    queryset = Project.objects.all().select_related("customer", "owner", "current_stage")
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['owner', 'current_stage', 'source']
    search_fields = ['name', 'customer_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    permission_classes = [IsAuthenticated, CachedModelPermissions]
    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).select_related('owner')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ActivityViewSet(viewsets.ModelViewSet):
    """
    行动记录视图集：支持增删改查
    """
    queryset = Activity.objects.all().select_related("project", "created_by")
    serializer_class = ActivitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'activity_type', 'created_by']
    search_fields = ['description', 'project__name']
    ordering_fields = ['activity_date', 'created_at']
    ordering = ['-activity_date']
    permission_classes = [IsAuthenticated, CachedModelPermissions]
    def get_queryset(self):
        return Activity.objects.filter(created_by=self.request.user).select_related('created_by')
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProjectStageViewSet(viewsets.ModelViewSet):
    queryset = ProjectStage.objects.all()
    serializer_class = ProjectStageSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]

