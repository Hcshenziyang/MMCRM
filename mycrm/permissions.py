from rest_framework.permissions import DjangoModelPermissions
from django.core.cache import cache


def get_user_perms(user):
    key = f"user:{user.id}:perms"
    perms = cache.get(key)
    if perms is None:
        perms = list(user.get_all_permissions())
        cache.set(key, perms, timeout=3600)  # 1小时过期，可调
    return perms


class CachedModelPermissions(DjangoModelPermissions):
    """
    等价于 DjangoModelPermissions，只是用缓存来减少数据库查询
    此外增加了 view相关权限的审查
    """
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    def get_required_permissions(self, method, model_cls):
        """
        按照请求方法，返回所需的权限列表
        """
        return [perm % {
            "app_label": model_cls._meta.app_label,
            "model_name": model_cls._meta.model_name,
        } for perm in self.perms_map.get(method, [])]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        queryset = self._queryset(view)
        perms = get_user_perms(request.user)
        required_perms = self.get_required_permissions(request.method, queryset.model)

        # 只要缺一个权限就拒绝
        return all(perm in perms for perm in required_perms)