from rest_framework import serializers
from django.contrib.auth.models import Group, Permission, User

# 权限管理
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']


# 用户管理
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email']


# 角色（组）管理 - 最终修正版
class GroupSerializer(serializers.ModelSerializer):
    # --- 用于“读取”的字段 ---
    users = UserSerializer(many=True, read_only=True, source='user_set')
    permissions = PermissionSerializer(many=True, read_only=True)

    # 用于“写入”的字段
    user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        source='user_set',  # 将传入的ID列表应用到 group.user_set 关系上
        required=False     # 设置为非必需，这样更新组名时就不用必须传用户列表
    )
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        source='permissions',  # 将传入的ID列表应用到 group.permissions 关系上
        required=False
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'users', 'permissions', 'user_ids', 'permission_ids']