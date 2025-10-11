from rest_framework import serializers
from django.contrib.auth.models import Group, Permission, User


class SimpleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']


class UserSerializer(serializers.ModelSerializer):
    groups_read = SimpleGroupSerializer(many=True, read_only=True, source='groups')
    groups_write = serializers.PrimaryKeyRelatedField(many=True, queryset=Group.objects.all(), write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'groups_read', 'groups_write']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # 密码只写，更新时非必需
        }

    def create(self, validated_data):
        groups_data = validated_data.pop('groups_write', [])  # 先取出groups数据
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)

        if password:
            user.set_password(password)
        user.groups.set(groups_data)
        user.save()
        return user

    def update(self, instance, validated_data):
        groups_data = validated_data.pop('groups_write', None)  # 先取出groups数据
        password = validated_data.pop('password', None)
        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        if groups_data is not None:  # 只有当 groups_write 被传入时才更新
            instance.groups.set(groups_data)

        instance.save()
        return instance


class GroupSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True, source='user_set')
    permissions = PermissionSerializer(many=True, read_only=True)
    user_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        write_only=True,
        source='user_set',
        required=False
    )
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        source='permissions',
        required=False
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'users', 'permissions', 'user_ids', 'permission_ids']