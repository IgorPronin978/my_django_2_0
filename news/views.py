import json

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from .models import Article, ArticleHistory, ArticleHistoryDetail, Category, Favorite, Like, Tag,  UserSubscription, TagSubscription
from .forms import ArticleForm, ArticleUploadForm, CommentForm
import unidecode
from django.utils.text import slugify

# Пример данных для новостей
info = {
    "users_count": get_user_model().objects.count(),
    "news_count": len(Article.objects.all()),
    "menu": [
        {"title": "Главная", "url": "/", "url_name": "index"},
        {"title": "О проекте", "url": "/about/", "url_name": "about"},
        {"title": "Каталог", "url": "/news/catalog/", "url_name": "news:catalog"},
    ],
}

class MenuMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(info)
        context['categories_with_count'] = Category.get_categories_with_news_count()
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context

class BaseArticleListView(MenuMixin, ListView):
    model = Article
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 9

    def get_queryset(self):
        queryset = Article.objects.select_related('category').prefetch_related('tags')
        return queryset.order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = Category.get_categories_with_news_count()
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context

class AllNewsView(MenuMixin, ListView):
    template_name = 'news/catalog.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        return Article.get_all_articles(
            sort=self.request.GET.get('sort', 'publication_date'),
            order=self.request.GET.get('order', 'desc')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context

class NewsByCategoryView(BaseArticleListView):
    def get_queryset(self):
        return Article.get_articles_by_category(self.kwargs['category_id'])

    def get_context_data(self, **kwargs):
         context = super().get_context_data(**kwargs)
         context['active_category_id'] = self.kwargs['category_id']
         return context

class NewsByTagView(BaseArticleListView):
    def get_queryset(self):
        return Article.get_articles_by_tag(self.kwargs['tag_id'])

    def get_context_data(self, **kwargs):
         context = super().get_context_data(**kwargs)
         tag = get_object_or_404(Tag, pk=self.kwargs["tag_id"])
         context["active_tag"] = tag
         if self.request.user.is_authenticated:
             context["is_subscribed_tag"] = TagSubscription.objects.filter(
                 subscriber=self.request.user,
                 tag=tag
             ).exists()
         else:
             context["is_subscribed_tag"] = False
         return context

class SearchNewsView(BaseArticleListView):
    def get_queryset(self):
        query = self.request.GET.get('q')
        return Article.search_articles(query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q')
        return context

class FavoritesView(BaseArticleListView):
    def get_queryset(self):
        ip_address = self.request.META.get('REMOTE_ADDR')
        return Article.get_favorite_articles(ip_address)

class ToggleView(View):
    model = None  # Модель, с которой работает toggle (Like или Favorite)
    article_field = 'article'  # Поле, связывающее модель с Article

    def post(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        ip_address = request.META.get('REMOTE_ADDR')
        obj, created = self.model.objects.get_or_create(**{self.article_field: article, 'ip_address': ip_address})
        if not created:
            obj.delete()
        is_toggled = self.model.objects.filter(**{self.article_field: article, 'ip_address': ip_address}).exists()
        return self.get_response(article, is_toggled)

    def get_response(self, article, is_toggled):
        raise NotImplementedError("Subclasses must implement get_response method")

class ToggleLikeView(ToggleView):
    model = Like

    def get_response(self, article, is_toggled):
        return JsonResponse({'likes_count': article.likes_count(), 'liked': is_toggled})

class ToggleFavoriteView(ToggleView):
    model = Favorite

    def get_response(self, article, is_toggled):
        return JsonResponse({'favorited': is_toggled})

class ArticleDetailView(MenuMixin, DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    pk_url_kwarg = 'article_id'  # Явно указываем имя параметра URL

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()

        # подписка на автора
        if self.request.user.is_authenticated and self.object.author:
            context["is_subscribed_author"] = UserSubscription.objects.filter(
                subscriber=self.request.user,
                author=self.object.author
            ).exists()
        else:
            context["is_subscribed_author"] = False

        context['comments'] = self.object.comments.all()
        context['categories_with_count'] = Category.get_categories_with_news_count()
        context['user_ip'] = self.request.META.get('REMOTE_ADDR')
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        self.object = self.get_object()
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = self.object
            comment.user = request.user
            comment.save()
            return redirect('news:detail_article_by_id', article_id=self.object.id)
        context = self.get_context_data(comment_form=comment_form)
        return self.render_to_response(context)

class MainView(MenuMixin, ListView):
    """
     Главная страница `/` – выводит статьи авторов/тегов,
     на которые подписан текущий пользователь.
     Если подписок нет — возвращает пустой QuerySet.
     """

    template_name = "news/catalog.html"
    paginate_by = 10
    context_object_name = "articles"

    def get_queryset(self):
        order_by = self.request.GET.get("order_by", "-publication_date")
        qs = Article.objects.select_related("category").prefetch_related("tags")

        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        author_ids = user.subscribed_authors.values_list("author_id", flat=True)
        tag_ids = user.subscribed_tags.values_list("tag_id", flat=True)

        if author_ids or tag_ids:
            qs = qs.filter(
                Q(author_id__in=author_ids) | Q(tags__id__in=tag_ids)
            ).distinct()
        else:
            qs = qs.none()

        return qs.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_feed"] = True          # признак «это лента подписок»
        context["active_tag"] = None       # чтобы шаблон не путал с тег‑страницей
        return context

class AboutView(MenuMixin, TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = Category.get_categories_with_news_count()
        return context

class DetailArticleByTitleView(MenuMixin, DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'title'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories_with_count'] = Category.get_categories_with_news_count()
        return context


def generate_unique_slug(title):
    base_slug = slugify(unidecode.unidecode(title))
    unique_slug = base_slug
    num = 1
    while Article.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{base_slug}-{num}"
        num += 1
    return unique_slug


class AddArticleView(LoginRequiredMixin, MenuMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/add_article.html'
    redirect_field_name = 'next'  # Имя параметра URL, используемого для перенаправления после успешного входа в систему
    success_url = reverse_lazy('news:catalog')

    def form_valid(self, form):
        form.instance.author = self.request.user
        # Если пользователь не модератор и не админ, устанавливаем статус "не проверено"
        if not (self.request.user.is_superuser or self.request.user.groups.filter(name="Moderator").exists()):
            form.instance.status = 0  # или False, в зависимости от типа поля
        return super().form_valid(form)

    def generate_unique_slug(self, title):
        base_slug = slugify(unidecode.unidecode(title))
        unique_slug = base_slug
        num = 1
        while Article.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1
        return unique_slug


class ArticleUpdateView(LoginRequiredMixin, MenuMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/edit_article.html'
    context_object_name = 'article'
    success_url = '/news/catalog/'

    def form_valid(self, form):
        # Получаем исходное состояние статьи до сохранения изменений
        original = self.get_object()
        old_data = {
            'title': original.title,
            'category': str(original.category),
            'tags': list(original.tags.values_list('name', flat=True)),
        }

        # Сохраняем изменения
        response = super().form_valid(form)

        # Получаем новые данные после сохранения
        new_data = {
            'title': self.object.title,
            'category': str(self.object.category),
            'tags': list(self.object.tags.values_list('name', flat=True)),
        }

        # Сравниваем старые и новые данные для отслеживаемых полей
        changes = {}
        for key in old_data:
            if old_data[key] != new_data[key]:
                changes[key] = (old_data[key], new_data[key])

        # Вывод для отладки (можно удалить после проверки)
        print("Old data:", old_data)
        print("New data:", new_data)
        print("Detected changes:", changes)

        # Если изменения обнаружены, создаём запись истории и детали изменений
        if changes:
            from .models import ArticleHistory, ArticleHistoryDetail  # если модели импортируются не глобально
            history = ArticleHistory.objects.create(article=self.object, user=self.request.user)
            for field, (old_val, new_val) in changes.items():
                # Если значение - список (например, теги), преобразуем его в строку
                if isinstance(old_val, list):
                    old_str = ', '.join(old_val)
                else:
                    old_str = old_val
                if isinstance(new_val, list):
                    new_str = ', '.join(new_val)
                else:
                    new_str = new_val
                ArticleHistoryDetail.objects.create(
                    history=history,
                    field_name=field,
                    old_value=old_str,
                    new_value=new_str,
                )
        return response

class ArticleDeleteView(LoginRequiredMixin, MenuMixin, DeleteView):
    model = Article
    template_name = 'news/delete_article.html'
    context_object_name = 'article'
    success_url = reverse_lazy('news:catalog')
    redirect_field_name = 'next'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.groups.filter(name="Moderator").exists():
            return qs
        return qs.filter(author=self.request.user)

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

class EditArticleFromJsonView(MenuMixin, FormView):
    template_name = 'news/edit_article_from_json.html'
    form_class = ArticleForm

    def get(self, request, *args, **kwargs):
        index = self.kwargs['index']
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
        context = {
            'form': form,
            'index': index,
            'total': len(articles_data),
            'is_last': index == len(articles_data) - 1
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        index = self.kwargs['index']
        articles_data = request.session.get('articles_data', [])
        article_data = articles_data[index]
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            if 'next' in request.POST:
                self.save_article(article_data, form)
                request.session['current_index'] = index + 1
                return redirect('news:edit_article_from_json', index=index + 1)
            elif 'save_all' in request.POST:
                self.save_article(article_data, form)
                for i in range(index + 1, len(articles_data)):
                    self.save_article(articles_data[i])
                del request.session['articles_data']
                del request.session['current_index']
                return redirect('news:catalog')
        context = {
            'form': form,
            'index': index,
            'total': len(articles_data),
            'is_last': index == len(articles_data) - 1
        }
        return render(request, self.template_name, context)

    def save_article(self, article_data, form=None):
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

    # ------------------  TOGGLE AUTHOR SUBSCRIPTION  -------------------


class ToggleAuthorSubscriptionView(LoginRequiredMixin, View):
    """
    POST‑эндпоинт/subscribe/author/<author_id>/.
    Переключает подписку текущего пользователя на автора.
    """

    def post(self, request, author_id, *args, **kwargs):
        sub, created = UserSubscription.objects.get_or_create(
            subscriber=request.user,
            author_id=author_id,
        )
        if not created:
            sub.delete()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    # ------------------  TOGGLE TAG SUBSCRIPTION  ----------------------


class ToggleTagSubscriptionView(LoginRequiredMixin, View):
    """
    POST‑эндпоинт/subscribe/tag/<tag_id>/.
    Переключает подписку на тег.
    """

    def post(self, request, tag_id, *args, **kwargs):
        sub, created = TagSubscription.objects.get_or_create(
            subscriber=request.user,
            tag_id=tag_id,
        )
        if not created:
            sub.delete()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))