#!/bin/sh

# 1. 执行数据迁移
echo "Running database migrations..."
python manage.py migrate --no-input

# 2. 收集 Admin 静态文件 (如果用了 Admin)
echo "Collecting static files..."
python manage.py collectstatic --no-input --clear

# 3. 启动 Gunicorn
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 mycrm.wsgi:application --workers 3
