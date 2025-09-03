from django.db import models

# Create your models here.
from django.db import models

class Customer(models.Model):
    id = models.AutoField(primary_key=True)  # 自增主键
    name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name