# 定义表单结构
# 处理数据验证
# 管理表单字段配置

from django import forms
from django.contrib.auth.models import User

def has_multiple_char_types(s):
    # 字符串判断
    types = set()
    for char in s:
        if char.isupper():
            types.add('大写')
        elif char.islower():
            types.add('小写')
        elif char.isdigit():
            types.add('数字')
        else:
            types.add('其他')  # 特殊字符（如标点、空格等）
    return len(types) < 2  # 至少存在两种类型

class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # 定义字符串类型用户名，限制长度，指定HTML中显示text，
    # attrs={'class': 'form-control'}则是限制样式
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    # 字段级验证，判断是否存在已有同名用户
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("用户名已存在")
        return username
    # 表单级验证，判断两次密码是否一致
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("两次密码不一致")

        if has_multiple_char_types(password):
            raise forms.ValidationError("密码需要两种及两种以上字符！")