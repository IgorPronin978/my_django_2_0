#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itg.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

User = get_user_model()

# Параметры суперпользователя
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpass')

# Создание суперпользователя
if not User.objects.filter(username=username).exists():
    print("Creating superuser...")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("Superuser already exists.")

# Настройка Site с ID=1
site, created = Site.objects.get_or_create(id=1, defaults={
    'domain': '127.0.0.1',
    'name': '127.0.0.1'
})

if not created:
    site.domain = '127.0.0.1'
    site.name = '127.0.0.1'
    site.save()
    print("Updated Site id=1 to 127.0.0.1")
else:
    print("Created Site id=1 with 127.0.0.1")

# Создание SocialApp для GitHub (только если есть все необходимые переменные)
client_id = os.environ.get('GITHUB_CLIENT_ID')  # Изменено с CLIENT_ID на GITHUB_CLIENT_ID
client_secret = os.environ.get('GITHUB_CLIENT_SECRET')  # Изменено с CLIENT_SECRET на GITHUB_CLIENT_SECRET

if client_id and client_secret:  # Проверяем наличие обоих значений
    if not SocialApp.objects.filter(provider='github', client_id=client_id).exists():
        print("Creating SocialApp for GitHub...")
        app = SocialApp.objects.create(
            provider='github',
            name='GitHub',
            client_id=client_id,
            secret=client_secret,
        )
        app.sites.add(site)
        print("Successfully created SocialApp for GitHub")
    else:
        print("SocialApp for GitHub already exists.")
else:
    print("Skipping GitHub SocialApp creation - missing GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET")