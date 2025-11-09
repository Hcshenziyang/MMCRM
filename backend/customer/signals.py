# customer/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Customer


@receiver([post_save, post_delete], sender=Customer)
def update_customer_version(sender, instance, **kwargs):
    """
    当 Customer 模型实例被保存或删除后，递增客户数据版本号
    """
    version_key = 'crm:customers:version'
    try:
        cache.incr(version_key)
    except ValueError:  # 如果键不存在，Django的cache.incr会抛出ValueError
        cache.set(version_key, 2)  # 设为2，因为初始版本是1

