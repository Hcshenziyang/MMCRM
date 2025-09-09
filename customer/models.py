from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    id = models.AutoField(primary_key=True)  # 自增主键
    name = models.CharField(max_length=150, blank=False, null=False)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    owner = models.ForeignKey(User, related_name='customers', on_delete=models.CASCADE)

    def __str__(self):
        return self.name