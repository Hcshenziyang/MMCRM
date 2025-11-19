#!/bin/sh
#!/bin/sh
set -e

echo "Waiting for MySQL..."
while ! nc -z db 3306; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

# Only seed once
if [ ! -f /app/.seeded ]; then
    echo "Loading initial data..."
    if [ -f /app/initial_data.json ]; then
        python manage.py loaddata initial_data.json
        touch /app/.seeded
        echo "Initial data loaded."
    else
        echo "initial_data.json not found, skipping."
    fi
else
    echo "Initial data already loaded. Skipping."
fi

echo "Starting gunicorn..."
exec gunicorn mycrm.wsgi:application --bind 0.0.0.0:8000 --workers 3
