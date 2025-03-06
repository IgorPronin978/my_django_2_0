from django import template
from news.models import Like

register = template.Library()

@register.filter(name='has_liked')
def has_liked(article, ip_address):
    print(f"Checking like for article {article.id} from IP {ip_address}")  # Отладочный вывод
    return Like.objects.filter(article=article, ip_address=ip_address).exists()