from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer, CustomerSerializer
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from .models import Customer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth.decorators import login_required
import requests
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import status
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from rest_framework.decorators import action

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
    permission_classes = [IsAuthenticated]  # 加上这行，给 API 上锁！

    def get_queryset(self):
        # 查询函数
        return Customer.objects.filter(owner=self.request.user)  # 只返回当前用户

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "请上传文件"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            wb = openpyxl.load_workbook(file)
            ws = wb.active
        except Exception as e:
            return Response({"error": f"文件解析失败：{str(e)}"},
                             status=status.HTTP_400_BAD_REQUEST)

        # 第一行是表头，从第二行开始
        created_count, updated_count = 0, 0
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row[1]:  # 必须有姓名
                continue
            customer_id, name, phone, email, address, owner_username, *_ = row

            # 如果有 ID，尝试更新；否则新建
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                    customer.name = name
                    customer.phone = phone
                    customer.email = email
                    customer.address = address
                    customer.save()
                    updated_count += 1
                except Customer.DoesNotExist:
                    continue
            else:
                Customer.objects.create(
                    name=name,
                    phone=phone,
                    email=email,
                    address=address,
                    owner=request.user  # 默认当前用户
                )
                created_count += 1

        return Response({
            "msg": "导入完成",
            "created": created_count,
            "updated": updated_count
        })

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Customers"

        # 表头
        headers = ["ID", "姓名", "电话", "邮箱", "地址", "负责人", "创建时间", "更新时间"]
        ws.append(headers)

        # 数据行
        for c in self.get_queryset():
            ws.append([
                c.id,
                c.name,
                c.phone,
                c.email,
                c.address,
                c.owner.username if c.owner else "",
                c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                c.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        # 设置列宽
        for i, col in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(i)].width = 20

        # 返回 response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response['Content-Disposition'] = 'attachment; filename=customers.xlsx'
        wb.save(response)
        return response
@login_required
def customer_list_view(request):
    customers = Customer.objects.filter(owner=request.user)
    return render(request, 'customer/customer_list.html', {'customers': customers})

