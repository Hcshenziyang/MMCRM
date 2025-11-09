from . import views
from .views import CustomersSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token


router = DefaultRouter()
router.register(r"customers", CustomersSet, basename="customer")

urlpatterns = [
    path("", include(router.urls)),
]