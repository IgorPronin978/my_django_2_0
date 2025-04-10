from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from allauth.account.models import EmailAddress
from django.db import transaction

from .models import Profile
from news.models import Category

User = get_user_model()

@receiver(post_save, sender=EmailAddress)
def update_verified_status(sender, instance, **kwargs):
    """
    Обновляет статус верификации email и синхронизирует с другими адресами пользователя
    """
    if instance.verified:
        print(f"[SIGNAL] Email подтвержден: {instance.email}")
        # Атомарная операция для избежания race condition
        with transaction.atomic():
            EmailAddress.objects.filter(
                user=instance.user
            ).exclude(pk=instance.pk).update(verified=True)

@receiver([post_save, post_delete], sender=Category)
def clear_category_cache(sender, **kwargs):
    """
    Очищает кеш категорий при изменении
    """
    cache.delete("categories")
    cache.delete("categories_menu")  # Добавляем дополнительный ключ, если используется

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Автоматически создает или обновляет профиль пользователя
    с обработкой возможных ошибок
    """
    try:
        with transaction.atomic():
            if created:
                Profile.objects.get_or_create(user=instance)
            elif hasattr(instance, 'profile'):
                instance.profile.save()
    except Exception as e:
        print(f"[SIGNAL] Ошибка при обработке профиля пользователя {instance}: {e}")

# Добавляем метод get_profile к модели User
def get_profile(self):
    """
    Безопасное получение профиля с автоматическим созданием при необходимости
    """
    try:
        return self.profile
    except Profile.DoesNotExist:
        with transaction.atomic():
            # Двойная проверка для избежания race condition
            profile, created = Profile.objects.get_or_create(user=self)
            return profile

User.add_to_class('get_profile', property(get_profile))