from django.contrib.auth.models import User, Group, Permission
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from mycrm.permissions import CachedModelPermissions

from .serializers import UserSerializer, GroupSerializer, PermissionSerializer

from django.db import connection


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]
