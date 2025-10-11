from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.views import View
# 重要的是在这里覆盖默认设置
from rest_framework.permissions import AllowAny  # 允许任何请求
from rest_framework_simplejwt.views import TokenRefreshView



class RegisterView(APIView):
    # 禁用全局认证类。对于登录视图，我们不期望有任何认证凭据。
    authentication_classes = []  # 空列表表示不使用任何认证类
    # 禁用全局权限类。登录视图应该允许任何人访问。
    permission_classes = [AllowAny]  # 允许所有用户访问，无论是否认证
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "注册成功，请登录！"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    # 禁用全局认证类。对于登录视图，我们不期望有任何认证凭据。
    authentication_classes = []  # 空列表表示不使用任何认证类
    # 禁用全局权限类。登录视图应该允许任何人访问。
    permission_classes = [AllowAny]  # 允许所有用户访问，无论是否认证
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({"error": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "登出成功"})
        response.delete_cookie('access_token')
        return response


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "缺少refresh token"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            response = super().post(request, *args, **kwargs)
            response.data['message'] = "令牌刷新成功"
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)