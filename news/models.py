import unidecode

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify


class AllArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class ArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    def sorted_by_date(self):
        return self.get_queryset().all().order_by('-title')


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Категория')

    def __str__(self):
        return self.name

    @classmethod
    def get_categories_with_news_count(cls):
        categories = cls.objects.all()
        categories_with_count = []
        for category in categories:
            news_count = Article.objects.filter(category=category).count()
            categories_with_count.append({
                'category': category,
                'news_count': news_count,
            })
        return categories_with_count

    class Meta:
        db_table = 'Categories'  # без указания этого параметра, таблица в БД будет называться вида 'news_categorys'
        verbose_name = 'Категория'  # единственное число для отображения в админке
        verbose_name_plural = 'Категории'  # множественное число для отображения в админке
        ordering = ['name']  # указывает порядок сортировки модели по умолчанию


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Тег')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Tags'  # без указания этого параметра, таблица в БД будет называться вида 'news_tags'
        verbose_name = 'Тег'  # единственное число для отображения в админке
        verbose_name_plural = 'Теги'  # множественное число для отображения в админке

class Article(models.Model):
    class Status(models.IntegerChoices):
        UNCHECKED = 0, 'не проверено'
        CHECKED = 1, 'проверено'

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    publication_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    views = models.IntegerField(default=0, verbose_name='Просмотры')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, default=1, verbose_name='Категория')
    tags = models.ManyToManyField('Tag', related_name='article', verbose_name='Теги')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    status = models.BooleanField(default=0,
                                 choices=(map(lambda x: (bool(x[0]), x[1]), Status.choices)),
                                 verbose_name='Проверено')

    author = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, default=None, verbose_name='Автор')

    image = models.ImageField(
        upload_to='articles/%Y/%m/%d',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )

    objects = ArticleManager()
    all_objects = AllArticleManager()

    def get_absolute_url(self):
        return reverse('news:detail_article_by_id', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
    # Сохраняем статью, чтобы получить id
        super().save(*args, **kwargs)
        if not self.slug:
            base_slug = slugify(unidecode.unidecode(self.title))
            unique_slug = base_slug
            num = 1
            while Article.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


    class Meta:
        db_table = 'Articles'  # без указания этого параметра, таблица в БД будет называться 'news_artcile'
        verbose_name = 'Статья'  # единственное число для отображения в админке
        verbose_name_plural = 'Статьи'  # множественное число для отображения в админке

        # ordering = ['publication_date']  # указывает порядок сортировки модели по умолчанию
        # unique_together = (...)  # устанавливает уникальность для комбинации полей
        # index_together = (...)  # создаёт для нескольких полей
        # indexes = (...)  # определяет пользовательские индексы
        # abstract = True/False  # делает модель абстрактной, не создаёт таблицу БД, нужна только для наследования другими моделями данных
        # managed = True/False  # будет ли эта модель управляться (создание, удаление, изменение) с помощью Django или нет
        # permissions = [...]  # определяет пользовательские разрешения для модели

    def __str__(self):
        return self.title

    def likes_count(self):
        return self.likes.count()

    def favorites_count(self):
        return self.favorites.count() # Используем related_name='favorites' для связи с моделью Favorite

    @classmethod
    def get_all_articles(cls, sort='publication_date', order='desc', category_id=None):
        valid_sort_fields = {'publication_date', 'views'}
        if sort not in valid_sort_fields:
            sort = 'publication_date'

        order_by = sort if order == 'asc' else f'-{sort}'

        queryset = cls.objects.select_related('category').prefetch_related('tags')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset.order_by(order_by)

    @classmethod
    def get_articles_by_category(cls, category_id):
        return cls.objects.filter(category_id=category_id).order_by('-publication_date')

    @classmethod
    def get_articles_by_tag(cls, tag_id):
        return cls.objects.filter(tags__id=tag_id).order_by('-publication_date')

    @classmethod
    def search_articles(cls, query):
        if query:
            return cls.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query))
        return cls.objects.all().order_by('-publication_date')

    @classmethod
    def get_favorite_articles(cls, ip_address):
        favorites = Favorite.objects.filter(ip_address=ip_address).values_list('article', flat=True)
        return cls.objects.filter(id__in=favorites).order_by('-publication_date')

    def likes_count(self):
        return self.likes.count()

    def favorites_count(self):
        return self.favorites.count()

class Like(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='likes')
    ip_address = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Likes'
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ('article', 'ip_address')  # Один пользователь может лайкнуть статью только один раз

    def __str__(self):
        return f"Like by {self.ip_address} on {self.article.title}"

class Favorite(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='favorites')
    ip_address = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        unique_together = ('article', 'ip_address')  # Один пользователь может добавить новость в избранное только один раз

    def __str__(self):
        return f"Favorite by {self.ip_address} on {self.article.title}"


class ArticleHistory(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='article_history')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.article.title} — {self.timestamp.strftime('%d %b %Y %H:%M')}"


class ArticleHistoryDetail(models.Model):
    history = models.ForeignKey(ArticleHistory, on_delete=models.CASCADE, related_name='details')
    field_name = models.CharField(max_length=100)  # например, title, category, tags и т.д.
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.field_name}: {self.old_value} → {self.new_value}"

class Comment(models.Model):
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='comments')
    content = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
            return f"Комментарий от {self.user or 'Аноним'} на {self.article.title}"

    class Meta:
        ordering = ('created_at',)
