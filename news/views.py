import json

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Article, Tag, Category, Like, Favorite
from django.http import JsonResponse, HttpResponseRedirect
from .forms import ArticleForm, ArticleUploadForm

import unidecode
from django.db import models
from django.utils.text import slugify

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


def edit_article_from_json(request, index):
    articles_data = request.session.get('articles_data', [])
    if index >= len(articles_data):
        return redirect('news:catalog')
    article_data = articles_data[index]
    form = ArticleForm(initial={
        'title': article_data['fields']['title'],
        'content': article_data['fields']['content'],
        'category': Category.objects.get(name=article_data['fields']['category']),
        'tags': [Tag.objects.get(name=tag) for tag in article_data['fields']['tags']]
    })
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            if 'next' in request.POST:
                # Сохраняем текущую статью
                save_article(article_data, form)
                # Переходим к следующей статье
                request.session['current_index'] = index + 1
                return redirect('news:edit_article_from_json', index=index + 1)
            elif 'save_all' in request.POST:
                # Сохраняем текущую статью
                save_article(article_data, form)
                # Сохраняем все оставшиеся статьи
                for i in range(index + 1, len(articles_data)):
                    save_article(articles_data[i])
                del request.session['articles_data']
                del request.session['current_index']
                return redirect('news:catalog')
    context = {'form': form, 'index': index, 'total': len(articles_data), 'is_last': index == len(articles_data) - 1}
    return render(request, 'news/edit_article_from_json.html', context)


def save_article(article_data, form=None):
    fields = article_data['fields']
    title = fields['title']
    content = fields['content']
    category_name = fields['category']
    tags_names = fields['tags']
    category = Category.objects.get(name=category_name)
    # Генерируем slug до создания статьи
    base_slug = slugify(unidecode.unidecode(title))
    unique_slug = base_slug
    num = 1
    while Article.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{base_slug}-{num}"
        num += 1
    if form:
        article = form.save(commit=False)
        article.slug = unique_slug
        article.save()
        # Обновляем теги
        article.tags.set(form.cleaned_data['tags'])
    else:
        article = Article(
            title=title,
            content=content,
            category=category,
            slug=unique_slug
        )
        article.save()
        # Добавляем теги к статье
        for tag_name in tags_names:
            tag = Tag.objects.get(name=tag_name)
            article.tags.add(tag)
    return article

def upload_json_view(request):
    if request.method == 'POST':
        form = ArticleUploadForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = form.cleaned_data['json_file']
            try:
                data = json.load(json_file)
                errors = form.validate_json_data(data)
                if errors:
                    return render(request, 'news/upload_json.html', {'form': form, 'errors': errors})
                    # Сохраняем данные в сессию для последовательного просмотра
                request.session['articles_data'] = data
                request.session['current_index'] = 0
                return redirect('news:edit_article_from_json', index=0)
            except json.JSONDecodeError:
                return render(request, 'news/upload_json.html', {'form': form, 'error': 'Неверный формат JSON-файла'})
    else:
        form = ArticleUploadForm()
    return render(request, 'news/upload_json.html', {'form': form})

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

def add_article(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article_data = {
                 'fields': {
                     'title': form.cleaned_data['title'],
                     'content': form.cleaned_data['content'],
                     'category': form.cleaned_data['category'].name,
                     'tags': [tag.name for tag in form.cleaned_data['tags']]
                 }
            }
            article = save_article(article_data, form)
            return redirect('news:detail_article_by_id', article_id=article.id)
    else:
        form = ArticleForm()  # Создаём пустую форму для GET-запросов

    context = {'form': form, 'menu': info['menu']}
    return render(request, 'news/add_article.html', context=context)


def article_update(request, article_id):
    article = get_object_or_404(Article, pk=article_id)

    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            return redirect('news:detail_article_by_id', article_id=article.id)
    else:
        form = ArticleForm(instance=article)
    context = {'form': form, 'menu': info['menu'], 'article': article}
    return render(request, 'news/edit_article.html', context=context)


def article_delete(request, article_id):
    article = get_object_or_404(Article, pk=article_id)

    if request.method == "POST":
        article.delete()
        return redirect('news:catalog')

    context = {'menu': info['menu'], 'article': article}
    return render(request, 'news/delete_article.html', context=context)

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
        print(f"Toggle like for article {article.id} from IP {ip_address}")  # Отладочный вывод

        like, created = Like.objects.get_or_create(article=article, ip_address=ip_address)
        if not created:
            like.delete()

        liked = Like.objects.filter(article=article, ip_address=ip_address).exists()
        print(f"Like status: {liked}")  # Отладочный вывод
        return JsonResponse({'likes_count': article.likes_count(), 'liked': liked})

class ToggleFavoriteView(View):
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        ip_address = request.META.get('REMOTE_ADDR')
        print(f"Toggle favorite for article {article.id} from IP {ip_address}")  # Отладочный вывод

        favorite, created = Favorite.objects.get_or_create(article=article, ip_address=ip_address)
        if not created:
            favorite.delete()

        favorited = Favorite.objects.filter(article=article, ip_address=ip_address).exists()
        print(f"Favorite status: {favorited}")  # Отладочный вывод
        return JsonResponse({'favorited': favorited})

class FavoritesView(BaseNewsView):
    def get(self, request):
        ip_address = request.META.get('REMOTE_ADDR')
        favorites = Favorite.objects.filter(ip_address=ip_address).values_list('article', flat=True)
        articles = Article.objects.filter(id__in=favorites).order_by('-publication_date')
        return self.render(request, articles)