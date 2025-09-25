from rest_framework import serializers
from .models import Customer
from django.contrib.auth.models import User

class CustomerSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'address',
            'owner',
            'created_at',
            'updated_at'
        ]
