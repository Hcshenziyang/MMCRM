from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, CustomerSerializer
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from .models import Customer

def has_multiple_char_types(s):
    # 字符串判断
    types = set()
    for char in s:
        if char.isupper():
            types.add('大写')
        elif char.islower():
            types.add('小写')
        elif char.isdigit():
            types.add('数字')
        else:
            types.add('其他')  # 特殊字符（如标点、空格等）
    return len(types) < 2  # 至少存在两种类型

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 验证通过，获取清理后数据
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            User.objects.create_user(username=username, password=password)
            messages.success(request, "注册成功，请登录！")
            return redirect("login")
    else:
        form = RegisterForm()  # 空表单
    return render(request, "customer/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "登录成功！")
            return redirect("home")
        else:
            messages.error(request, "用户名或密码错误")
            return render(request, "customer/login.html",{"form_errors": "用户名或密码错误"})
    return render(request, "customer/login.html")

def logout_view(request):
    logout(request)
    return redirect("login")


def home_view(request):
    return render(request, "customer/home.html")


# 类视图
class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    # 确保只有登录的用户能访问

    def get(self, request):
        # 使用当前用户数据序列化
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CustomersSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "email", "phone", "address"]
    ordering_fields = ["created_at", "updated_at", "name"]
    # 启用 DRF 自带的过滤后端。
    # SearchFilter：允许在 URL 上用 ?search=关键字 来搜索数据。
    # OrderingFilter：允许在 URL 上用 ?ordering=字段名 来排序。

    def get_queryset(self):
        return Customer.objects.all()
        # return Customer.objects.filter(owner=self.request.user)  # 只返回当前用户

    def perform_create(self, serializer):
        serializer.save()
        # perform_create 是 DRF 在执行 create() 方法时会调用的钩子。
        # 默认 serializer.save() 就会把数据存进数据库。