from . import views
from .views import CurrentUserAPIView, CustomersSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token


router = DefaultRouter()
router.register(r"customers", CustomersSet, basename="customer")

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.home_view, name="home"),
    path("api/", include(router.urls)),
    path('customers/', views.customer_list_view, name='customer_list'),
]