FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    libmariadb-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project
COPY . /app/
RUN useradd -m appuser
USER appuser

# Expose port (gunicorn will use 8000)
EXPOSE 8000

# Run gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mycrm.wsgi:application", "--workers", "3"]
