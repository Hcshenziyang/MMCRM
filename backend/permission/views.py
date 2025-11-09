from django.contrib.auth.models import User, Group, Permission
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from mycrm.permissions import CachedModelPermissions
from django.db.models import Prefetch
from .serializers import UserSerializer, GroupSerializer, PermissionSerializer


class UserViewSet(viewsets.ModelViewSet):
    # queryset = User.objects.all()
    queryset = User.objects.all().prefetch_related('groups')  # 优化
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]

class GroupViewSet(viewsets.ModelViewSet):
    # queryset = Group.objects.all()
    # queryset = Group.objects.all().prefetch_related('user_set', 'permissions')  # 优化
    # 再优化
    queryset = Group.objects.prefetch_related('permissions',
                                              Prefetch('user_set',
                                                       queryset=User.objects.prefetch_related('groups')))
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]


class GroupViewSet(viewsets.ModelViewSet):
    # queryset = Group.objects.all().prefetch_related('user_set', 'permissions') # 这是之前的版本

    # --- 优化后的版本 ---
    queryset = Group.objects.prefetch_related('permissions',Prefetch('user_set', queryset=User.objects.prefetch_related('groups')))

    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, CachedModelPermissions]