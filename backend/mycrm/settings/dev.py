# mycrm/settings/dev.py
from .base import *

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key")



