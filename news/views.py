from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Article, Tag, Category, Like
from django.http import JsonResponse

# Пример данных для новостей
info = {
    "users_count": 'нету',
    "news_count": 'много',
    "menu": [
        {"title": "Главная", "url": "/", "url_name": "index"},
        {"title": "О проекте", "url": "/about/", "url_name": "about"},
        {"title": "Каталог", "url": "/news/catalog/", "url_name": "news:catalog"},
    ],
}

def get_categories_with_news_count():
    categories = Category.objects.all()
    categories_with_count = []
    for category in categories:
        news_count = Article.objects.filter(category=category).count()
        categories_with_count.append({
            'category': category,
            'news_count': news_count,
        })
    return categories_with_count

# Функция для главной страницы
def main(request):
    """
    Представление для главной страницы.
    """
    categories_with_count = get_categories_with_news_count()
    context = {**info, 'categories_with_count': categories_with_count}
    return render(request, 'main.html', context)

# Функция для страницы "О проекте"
def about(request):
    """
    Представление для страницы "О проекте".
    """
    categories_with_count = get_categories_with_news_count()
    context = {**info, 'categories_with_count': categories_with_count}
    return render(request, 'about.html', context)

class PaginatedView:
    paginate_by = 9

    def paginate_queryset(self, queryset, request):
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get('page')
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return page_obj

class BaseNewsView(View, PaginatedView):  # Наследуемся от View
    template_name = 'news/catalog.html'

    def get_context_data(self, **kwargs):
        context = {
            **info,
            'categories_with_count': get_categories_with_news_count(),
            'news_count': kwargs.get('news_count', 0),
            'news': kwargs.get('page_obj'),
            'user_ip': self.request.META.get('REMOTE_ADDR'),  # Добавляем IP пользователя в контекст
        }
        return context

    def render(self, request, queryset, extra_context=None):
        page_obj = self.paginate_queryset(queryset, request)
        context = self.get_context_data(page_obj=page_obj, news_count=len(queryset))
        if extra_context:
            context.update(extra_context)
        return render(request, self.template_name, context)

class AllNewsView(BaseNewsView):  # Наследуемся от BaseNewsView
    def get(self, request):
        sort = request.GET.get('sort', 'publication_date')
        order = request.GET.get('order', 'desc')
        category_id = request.GET.get('category')

        valid_sort_fields = {'publication_date', 'views'}
        if sort not in valid_sort_fields:
            sort = 'publication_date'

        order_by = sort if order == 'asc' else f'-{sort}'

        if category_id:
            articles = Article.objects.filter(category_id=category_id).order_by(order_by)
        else:
            articles = Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

        return self.render(request, articles)

class NewsByCategoryView(BaseNewsView):  # Наследуемся от BaseNewsView
    def get(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        articles = Article.objects.filter(category=category).order_by('-publication_date')
        extra_context = {'category': category}
        return self.render(request, articles, extra_context)

class NewsByTagView(BaseNewsView):  # Наследуемся от BaseNewsView
    def get(self, request, tag_id):
        tag = get_object_or_404(Tag, id=tag_id)
        articles = Article.objects.filter(tags=tag).order_by('-publication_date')
        extra_context = {'tag': tag}
        return self.render(request, articles, extra_context)

class SearchNewsView(BaseNewsView):  # Наследуемся от BaseNewsView
    paginate_by = 9

    def get(self, request):
        query = request.GET.get('q')
        if query:
            articles = Article.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).order_by('-publication_date')
        else:
            articles = Article.objects.all().order_by('-publication_date')

        extra_context = {'query': query}
        return self.render(request, articles, extra_context)

class DetailArticleByIdView(View):
    def get(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        article.views += 1
        article.save()
        categories_with_count = get_categories_with_news_count()
        context = {
            **info,
            'article': article,
            'categories_with_count': categories_with_count,
            'user_ip': request.META.get('REMOTE_ADDR'), # Убедитесь, что IP передается -->
        }
        return render(request, 'news/article_detail.html', context)

class DetailArticleByTitleView(View):
    def get(self, request, title):
        article = get_object_or_404(Article, slug=title)
        categories_with_count = get_categories_with_news_count()
        context = {**info, 'article': article, 'categories_with_count': categories_with_count}
        return render(request, 'news/article_detail.html', context)

class ToggleLikeView(View):
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        ip_address = request.META.get('REMOTE_ADDR')

        like, created = Like.objects.get_or_create(article=article, ip_address=ip_address)
        if not created:
            like.delete()

        return JsonResponse({'likes_count': article.likes_count(), 'liked': created})