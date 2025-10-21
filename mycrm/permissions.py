from rest_framework.permissions import DjangoModelPermissions
from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group, Permission
from django.core.cache import cache


def clear_user_perm_cache(user):
    key = f"user:{user.id}:perms"
    cache.delete(key)


# 当用户的权限直接变更时
@receiver(m2m_changed, sender=User.user_permissions.through)
def user_permissions_changed(sender, instance, **kwargs):
    clear_user_perm_cache(instance)


# 当用户所属组（Group）变化时
@receiver(m2m_changed, sender=User.groups.through)
def user_groups_changed(sender, instance, **kwargs):
    clear_user_perm_cache(instance)


# 当组的权限发生变化时（影响到组内所有用户）
@receiver(m2m_changed, sender=Group.permissions.through)
def group_permissions_changed(sender, instance, **kwargs):
    # instance 是 Group
    users = instance.user_set.all()
    for user in users:
        clear_user_perm_cache(user)

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