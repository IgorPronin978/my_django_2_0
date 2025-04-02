from django import template
from news.models import Like, Favorite

register = template.Library()

@register.filter(name='has_liked')
def has_liked(article, ip_address):
    print(f"Checking like for article {article.id} from IP {ip_address}")  # Отладочный вывод
    return Like.objects.filter(article=article, ip_address=ip_address).exists()

@register.filter(name='has_favorited')
def has_favorited(article, ip_address):
    return Favorite.objects.filter(article=article, ip_address=ip_address).exists()

@register.filter
def add(value, arg):
    return int(value) + int(arg)


@register.filter(name='can_edit')
def can_edit(article, user):
    """
    Возвращает True, если пользователь может редактировать (или удалять) статью.
    Условие:
      - пользователь аутентифицирован, и
      - либо он является суперпользователем,
      - либо состоит в группе "Moderator",
      - либо является автором статьи.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name="Moderators").exists():
        return True
    return article.author == user