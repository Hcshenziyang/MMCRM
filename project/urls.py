from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ActivityViewSet, ProjectStageViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'stages', ProjectStageViewSet, basename='stage')
urlpatterns = [
    path('', include(router.urls)),
]
