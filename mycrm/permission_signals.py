from django.db.models.signals import m2m_changed, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User, Group, Permission
from django.core.cache import cache

def clear_user_perm_cache(user):
    key = f"user:{user.id}:perms"
    cache.delete(key)

@receiver(m2m_changed, sender=User.user_permissions.through)
def user_permissions_changed(sender, instance, **kwargs):
    clear_user_perm_cache(instance)

@receiver(m2m_changed, sender=User.groups.through)
def user_groups_changed(sender, instance, **kwargs):
    clear_user_perm_cache(instance)

@receiver(m2m_changed, sender=Group.permissions.through)
def group_permissions_changed(sender, instance, **kwargs):
    # instance 是 Group
    users = instance.user_set.all()
    for user in users:
        clear_user_perm_cache(user)
