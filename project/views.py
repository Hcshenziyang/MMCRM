# project/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Project, Activity
from .serializers import ProjectSerializer, ActivitySerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """
    项目视图集：支持增删改查、阶段流转、筛选、搜索
    """
    queryset = Project.objects.all().select_related("customer", "owner", "current_stage")
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['owner', 'current_stage', 'source']
    search_fields = ['name', 'customer__name']
    ordering_fields = ['created_at', 'expected_close_date', 'actual_close_date']
    ordering = ['-created_at']

    # @action(detail=True, methods=["post"])
    # def move_stage(self, request, pk=None):
    #     """
    #     自定义动作：修改项目阶段
    #     POST /projects/{id}/move_stage/
    #     {
    #       "stage_id": 3
    #     }
    #     """
    #     project = self.get_object()
    #     stage_id = request.data.get("stage_id")
    #     if not stage_id:
    #         return Response({"detail": "缺少参数 stage_id"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     from .models import ProjectStage
    #     try:
    #         stage = ProjectStage.objects.get(pk=stage_id)
    #     except ProjectStage.DoesNotExist:
    #         return Response({"detail": "无效的 stage_id"}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     project.current_stage = stage
    #     project.save(update_fields=["current_stage", "updated_at"])
    #     return Response(ProjectSerializer(project).data)
    #
    # @action(detail=True, methods=["get"])
    # def timeline(self, request, pk=None):
    #     """
    #     自定义动作：获取项目的最新行动记录（默认10条）
    #     GET /projects/{id}/timeline/
    #     """
    #     project = self.get_object()
    #     limit = int(request.query_params.get("limit", 10))
    #     activities = project.activities.all().order_by("-activity_date")[:limit]
    #     return Response(ActivitySerializer(activities, many=True).data)


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
