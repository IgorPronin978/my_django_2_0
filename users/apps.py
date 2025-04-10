from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи и профили'  # Добавляем человекочитаемое имя

    def ready(self):
        # Импортируем сигналы только после полной загрузки приложения
        import users.signals  # noqa

        # Для дополнительной безопасности можно добавить проверку
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not hasattr(User, 'get_profile'):
                from .signals import get_profile
                User.add_to_class('get_profile', property(get_profile))
        except Exception as e:
            print(f"Ошибка при инициализации сигналов: {e}")