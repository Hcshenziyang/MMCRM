import os
from datetime import timedelta
from pathlib import Path
from decouple import config

# 获取路径，resolve解析为绝对路径，.parent获取当前路径的父目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# cast类型转换参数，转换为bool类型
DEBUG = config("DEBUG", default=True, cast=bool)

# 允许访问项目的主机/域名
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")

# 可以理解为项目的import，导入项目需要的模块和app
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "customer",
    "rest_framework",
    "permission",
    'rest_framework_simplejwt',
    'user',
    'project',
    'django_filters',
    'corsheaders',
    'aihelper',
]

# 同样类似于项目的import，不过导入的是中间件
MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

]

# 项目主URL配置模块路径，项目会导入mycrm/urls.py作为起点
ROOT_URLCONF = "mycrm.urls"

# 指定项目的WSGI应用入口点，用于连接Web服务器（如Gunicorn）和项目
WSGI_APPLICATION = "mycrm.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,  # 保留 True，让 Django Admin 能工作
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# 数据库配置
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DATABASE_NAME", default="mydb"),
        "USER": config("DATABASE_USER", default="root"),
        "PASSWORD": config("DATABASE_PASSWORD", default="123456"),
        "HOST": config("DATABASE_HOST", default="localhost"),
        "PORT": config("DATABASE_PORT", default="3306"),
    }
}

LANGUAGE_CODE = "zh-hans"  # django项目的默认语言，此处使用简体中文
TIME_ZONE = "Asia/Shanghai"  # 指定默认时区
USE_I18N = True  # 启动或者禁用Django国际化支持
USE_TZ = False  # 禁用时区支持，所有时间、日期采用TIME_ZONE

STATIC_URL = "/static/"  # 静态资源路径，不过本项目前后端分离，貌似没啥用
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---- CORS ----
# 定义一个变量，指定是否允许所有来源的跨域
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)
# 定义一个变脸，指定列表，允许的跨域请求具体来源
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="http://localhost:8080", cast=str).split(",")


# 配置自增字段，用于标准化和优化数据库主键行为，BigAutoField 64位整数，避免大型项目ID溢出
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# JWT配置
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Redis配置
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('REDIS_HOST', default='127.0.0.1')}:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": config("REDIS_PASSWORD", default=""),  # 可选
        },
        "TIMEOUT": config("CACHE_TIMEOUT", default=600, cast=int),  # 10分钟默认
    }
}

