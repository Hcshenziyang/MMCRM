from rest_framework import serializers
from django.contrib.auth.models import User


# 用户序列化器
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        """
        使用create_user覆写create函数，密码加密。
        """
        user = User.objects.create_user(**validated_data)
        return user