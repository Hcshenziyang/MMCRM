from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


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
        username = request.POST["username"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        form_errors = {}  # 存储各种错误类型

        # 用户名检查
        if not username:
            form_errors["username"] = "用户名不能为空！"
        elif User.objects.filter(username=username).exists():
            form_errors["username"] = "用户名已存在！"

        # 密码检查
        if not password:
            form_errors["password"] = "密码不能为空！"
        elif len(password) < 8:
            form_errors["password"] = "密码不能少于8位！"
        elif has_multiple_char_types(password):
            form_errors["password"] = "密码需要大写、小写、数字、特殊符号组合！"

        # 确认密码检查
        if password != confirm_password:
            form_errors["confirm_password"] = "两次密码输入不一致"

        if form_errors:
            # 如果有错误，返回注册页并传递错误信息
            return render(request, "customer/register.html", {"form_errors": form_errors})

        User.objects.create_user(username=username, password=password)
        messages.success(request, "注册成功，请登录！")
        return redirect("login")

    return render(request, "customer/register.html")


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
