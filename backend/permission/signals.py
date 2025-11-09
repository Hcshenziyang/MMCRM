# permission/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth.models import Group, Permission, User


@receiver([post_save, post_delete], sender=Group)
@receiver([post_save, post_delete], sender=User)
@receiver([post_save, post_delete], sender=Permission)
def update_permission_version(sender, instance, **kwargs):
    """
    当 Customer / Project / Activity 任意模型保存或删除后，
    递增客户数据版本号（用于前端缓存失效）
    """
    permissionversion_key = 'crm:permission:version'
    try:
        cache.incr(permissionversion_key)
    except ValueError:
        cache.set(permissionversion_key, 2)  # 初始版本是 1
