# users/backends.py
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache


class CachedPermissionsBackend(ModelBackend):
    # Django 3.x+ 把 _get_user_permissions 和 _get_group_permissions 合并到了 _get_permissions
    def _get_permissions(self, user_obj, obj, from_name):
        # from_name 可以是 'user' 或 'group'
        cache_key = f'{from_name}_perms:{user_obj.pk}'
        permissions = cache.get(cache_key)

        if permissions is None:
            # 调用父类的方法来实际查询数据库
            permissions = super()._get_permissions(user_obj, obj, from_name)
            # 写入缓存，比如5分钟
            cache.set(cache_key, permissions, timeout=300)

        return permissions

    # 你需要根据你的 Django 版本覆盖对应的方法
    # 对于老版本 Django，你可能需要像上面一样分别覆盖 _get_user_permissions 和 _get_group_permissions
    # 对于新版本 Django (>=3.x), 覆盖 _get_permissions 更佳