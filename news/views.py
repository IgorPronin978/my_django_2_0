import json
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Article, Tag, Category, Like, Favorite
from .forms import ArticleForm, ArticleUploadForm
import unidecode
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

class MenuMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(info)
        return context

class MainView(MenuMixin, TemplateView):
    template_name = 'main.html'  # Укажите ваш шаблон для главной страницы

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = get_categories_with_news_count()
        return context

class AboutView(MenuMixin, TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = get_categories_with_news_count()
        return context

class AllNewsView(MenuMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 9

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'publication_date')
        order = self.request.GET.get('order', 'desc')
        category_id = self.request.GET.get('category')

        valid_sort_fields = {'publication_date', 'views'}
        if sort not in valid_sort_fields:
            sort = 'publication_date'

        order_by = sort if order == 'asc' else f'-{sort}'

        if category_id:
            return Article.objects.filter(category_id=category_id).order_by(order_by)
        return Article.objects.select_related('category').prefetch_related('tags').order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = get_categories_with_news_count()
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context

class NewsByCategoryView(MenuMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(Category, id=self.kwargs['category_id'])
        return Article.objects.filter(category=self.category).order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class NewsByTagView(MenuMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 9

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, id=self.kwargs['tag_id'])
        return Article.objects.filter(tags=self.tag).order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

class SearchNewsView(MenuMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 9

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Article.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).order_by('-publication_date')
        return Article.objects.all().order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q')
        return context

class DetailArticleByIdView(MenuMixin, DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    pk_url_kwarg = 'article_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = get_categories_with_news_count()
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context

class DetailArticleByTitleView(MenuMixin, DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'title'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = get_categories_with_news_count()
        return context

class ToggleLikeView(View):
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        ip_address = request.META.get('REMOTE_ADDR')
        like, created = Like.objects.get_or_create(article=article, ip_address=ip_address)
        if not created:
            like.delete()
        liked = Like.objects.filter(article=article, ip_address=ip_address).exists()
        return JsonResponse({'likes_count': article.likes_count(), 'liked': liked})

class ToggleFavoriteView(View):
    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        ip_address = request.META.get('REMOTE_ADDR')
        favorite, created = Favorite.objects.get_or_create(article=article, ip_address=ip_address)
        if not created:
            favorite.delete()
        favorited = Favorite.objects.filter(article=article, ip_address=ip_address).exists()
        return JsonResponse({'favorited': favorited})

class FavoritesView(MenuMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 9

    def get_queryset(self):
        ip_address = self.request.META.get('REMOTE_ADDR')
        favorites = Favorite.objects.filter(ip_address=ip_address).values_list('article', flat=True)
        return Article.objects.filter(id__in=favorites).order_by('-publication_date')

class AddArticleView(MenuMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/add_article.html'
    success_url = '/news/catalog/'

class ArticleUpdateView(MenuMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/edit_article.html'
    context_object_name = 'article'

    def get_success_url(self):
        return reverse('news:detail_article_by_id', kwargs={'article_id': self.object.id})

class ArticleDeleteView(MenuMixin, DeleteView):
    model = Article
    template_name = 'news/delete_article.html'
    context_object_name = 'article'
    success_url = '/news/catalog/'

class UploadJsonView(MenuMixin, FormView):
    form_class = ArticleUploadForm
    template_name = 'news/upload_json.html'
    success_url = '/news/catalog/'

    def form_valid(self, form):
        json_file = form.cleaned_data['json_file']
        try:
            data = json.load(json_file)
            errors = form.validate_json_data(data)
            if errors:
                return self.render_to_response(self.get_context_data(form=form, errors=errors))
            self.request.session['articles_data'] = data
            self.request.session['current_index'] = 0
            return redirect('news:edit_article_from_json', index=0)
        except json.JSONDecodeError:
            return self.render_to_response(self.get_context_data(form=form, error='Неверный формат JSON-файла'))

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
                save_article(article_data, form)
                request.session['current_index'] = index + 1
                return redirect('news:edit_article_from_json', index=index + 1)
            elif 'save_all' in request.POST:
                save_article(article_data, form)
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
        article.tags.set(form.cleaned_data['tags'])
    else:
        article = Article(
            title=title,
            content=content,
            category=category,
            slug=unique_slug
        )
        article.save()
        for tag_name in tags_names:
            tag = Tag.objects.get(name=tag_name)
            article.tags.add(tag)
    return article