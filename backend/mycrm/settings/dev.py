# mycrm/settings/dev.py
from .base import *

MIDDLEWARE.append('silk.middleware.SilkyMiddleware')  # 测试工具
INSTALLED_APPS.append('silk')

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")

