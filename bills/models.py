from django.db import models

# Create your models here.
class Bill(models.Model):
    user = models.CharField(max_length=30)
    amount = models.FloatField()
    category = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    create_time = models.DateTimeField(auto_now_add=True)