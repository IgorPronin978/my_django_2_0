from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from .models import Article, Tag, Category

# Пример данных для новостей
info = {
    "users_count": 5,
    "news_count": 10,
    "menu": [
        {"title": "Главная",
         "url": "/",
         "url_name": "index"},
        {"title": "О проекте",
         "url": "/about/",
         "url_name": "about"},
        {"title": "Каталог",
         "url": "/news/catalog/",
         "url_name": "news:catalog"},
    ],
}

def get_categories_with_news_count():
    """
    Возвращает список категорий с количеством новостей в каждой категории.
    """
    categories = Category.objects.all()
    categories_with_count = []
    for category in categories:
        news_count = Article.objects.filter(category=category).count()
        categories_with_count.append({
            'category': category,
            'news_count': news_count,
        })
    return categories_with_count

def main(request):
    """
    Представление рендерит шаблон main.html
    """
    categories_with_count = get_categories_with_news_count()
    context = {**info, 'categories_with_count': categories_with_count}
    return render(request, 'main.html', context=context)

def about(request):
    """Представление рендерит шаблон about.html"""
    categories_with_count = get_categories_with_news_count()
    context = {**info, 'categories_with_count': categories_with_count}
    return render(request, 'about.html', context=context)

def catalog(request):
    categories_with_count = get_categories_with_news_count()
    context = {**info, 'categories_with_count': categories_with_count}
    return HttpResponse('Каталог новостей')

def get_categories(request):
    """
    Возвращает все категории для представления в каталоге
    """
    return HttpResponse('All categories')

def get_news_by_category(request, category_id):
    """
    Возвращает новости по категории для представления в каталоге
    """
    category = get_object_or_404(Category, id=category_id)
    articles = Article.objects.filter(category=category).order_by('-publication_date')
    categories_with_count = get_categories_with_news_count()

    context = {
        **info,
        'news': articles,
        'news_count': len(articles),
        'category': category,
        'categories_with_count': categories_with_count,
    }

    return render(request, 'news/catalog.html', context=context)

def get_news_by_tag(request, tag_id):
    """
    Возвращает новости по тегу для представления в каталоге
    """
    tag = get_object_or_404(Tag, id=tag_id)  # Используем id для поиска тега
    articles = Article.objects.filter(tags=tag).order_by('-publication_date')
    categories_with_count = get_categories_with_news_count()

    context = {
        **info,
        'news': articles,
        'news_count': len(articles),
        'tag': tag,
        'categories_with_count': categories_with_count,
    }

    return render(request, 'news/catalog.html', context=context)

def get_category_by_name(request, slug):
    return HttpResponse(f"Категория {slug}")

def get_all_news(request):
    sort = request.GET.get('sort', 'publication_date')  # сортировка по умолчанию
    order = request.GET.get('order', 'desc')  # направление сортировки по умолчанию
    category_id = request.GET.get('category')  # получаем ID категории

    # Проверяем, что сортировка допустима
    valid_sort_fields = {'publication_date', 'views'}
    if sort not in valid_sort_fields:
        sort = 'publication_date'

    # Определяем направление сортировки
    if order == 'asc':
        order_by = sort
    else:
        order_by = f'-{sort}'

    # Фильтруем новости по категории, если передан category_id
    if category_id:
        articles = Article.objects.filter(category_id=category_id).order_by(order_by)
    else:
        articles = Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

    categories_with_count = get_categories_with_news_count()

    context = {
        **info,
        'news': articles,
        'news_count': len(articles),
        'categories_with_count': categories_with_count,
    }

    return render(request, 'news/catalog.html', context=context)

def get_detail_article_by_id(request, article_id):
    """
    Возвращает детальную информацию по новости для представления
    """
    article = get_object_or_404(Article, id=article_id)
    categories_with_count = get_categories_with_news_count()

    context = {**info, 'article': article, 'categories_with_count': categories_with_count}

    return render(request, 'news/article_detail.html', context=context)

def get_detail_article_by_title(request, title):
    """
    Возвращает детальную информацию по новости для представления
    """
    article = get_object_or_404(Article, slug=title)
    categories_with_count = get_categories_with_news_count()

    context = {**info, 'article': article, 'categories_with_count': categories_with_count}

    return render(request, 'news/article_detail.html', context=context)