#!/usr/bin/env python
import os
import django
from django.contrib.auth import get_user_model

# Указываем модуль настроек проекта (замените "myproject" на имя вашего проекта)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itg.settings")
django.setup()

User = get_user_model()
# Создаем суперпользователя, если он еще не существует
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", "password")
    print("Superuser created.")
else:
    print("Superuser already exists.")