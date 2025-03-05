from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter

from .models import Article, Category, Tag

from .models import Like


admin.site.site_header = "Управа My Blog Admin"
admin.site.site_title = "Управа"
admin.site.index_title = "Здрав буди, админ!"


class ArticleStorkFilter(SimpleListFilter):
    title = 'Аисты в гнезде'
    parameter_name = 'has_storks'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть'),
            ('no', 'Нет')
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(content__contains='аисты')
        if self.value() == 'no':
            return queryset.exclude(content__contains='аисты')
        return queryset


class TagInline(admin.TabularInline):
    model = Article.tags.through
    extra = 1


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # list_display отображает поля в таблице
    list_display = ('pk', 'title', 'category', 'publication_date', 'views', 'status', 'is_active', 'has_storks')
    # list_display_links позволяет указать в качестве ссылок на объект другие поля
    list_display_links = ('pk',)
    # list_filter позволяет фильтровать по полям
    list_filter = ('category', 'is_active', 'status', ArticleStorkFilter)
    # сортировка, возможна по нескольким полям, по возрастанию или по убыванию
    ordering = ('category', '-is_active')
    # search_fields позволяет искать по полям
    search_fields = ('title', 'content')
    # actions позволяет выполнять действия над выбранными записями
    actions = ('make_inactive', 'make_active', 'set_checked', 'set_unchecked')
    list_per_page = 15
    # включение иерархического отображения по дате
    date_hierarchy = 'publication_date'
    # перенос кнопок сохранения в верхнюю часть формы
    save_on_top = True
    # fields позволяет выбирать поля для редактирования (не fieldsets)
    # fields = ('title', 'category', 'content', 'tags', 'is_active')

    # fieldsets позволяет выбирать группы полей (не работает с fields)
    fieldsets = (
        ('Главная информация', {'fields': ('title', 'content')}),
        ('Настройки фильтрации', {'fields': ('category', 'is_active', 'status')}),
        ('Доп. инфо', {'fields': ('views', 'slug')}),
    )

    # inlines позволяет добавлять дополнительные поля
    inlines = [TagInline]

    readonly_fields = ('views', 'slug')

    def get_queryset(self, request):
        return Article.all_objects.get_queryset()

    @admin.display(description='Аисты в гнезде')
    def has_storks(self, article):
        return 'Да' if 'аисты' in article.content else 'Нет'

    @admin.action(description='Сделать неактивными выбранные статьи')
    def make_inactive(modeladmin, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Сделать активными выбранные статьи')
    def make_active(modeladmin, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Отметить статьи как проверенные')
    def set_checked(self, request, queryset):
        updated = queryset.update(status=Article.Status.CHECKED)
        self.message_user(request, f'{updated} статей было отмечено как проверенные')

    @admin.action(description='Отметить статьи как не проверенные')
    def set_unchecked(self, request, queryset):
        updated = queryset.update(status=Article.Status.UNCHECKED)
        self.message_user(request, f'{updated} статей было отмечено как не проверенные', 'warning')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('article', 'ip_address', 'created_at')

admin.site.register(Category)
admin.site.register(Tag)
