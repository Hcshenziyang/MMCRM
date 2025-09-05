from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegisterForm

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
            messages.success(request,"登录成功！")
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
