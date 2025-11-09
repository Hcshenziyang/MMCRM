from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),         # Django 自带后台
    path("", include("user.urls")),      # 把根路径交给 user.urls 管理
    path("permission/", include("permission.urls")),
    path("customer/", include("customer.urls")),
    path("project/", include("project.urls")),
]

