from django.urls import path
from .views import (
    AllNewsView,
    NewsByCategoryView,
    NewsByTagView,
    SearchNewsView,
    DetailArticleByIdView,
    DetailArticleByTitleView,
    ToggleLikeView,
)

app_name = 'news'
urlpatterns = [
    path('catalog/', AllNewsView.as_view(), name='catalog'),
    path('catalog/<int:article_id>/', DetailArticleByIdView.as_view(), name='detail_article_by_id'),
    path('catalog/<slug:title>/', DetailArticleByTitleView.as_view(), name='detail_article_by_title'),
    path('tag/<int:tag_id>/', NewsByTagView.as_view(), name='get_news_by_tag'),
    path('category/<int:category_id>/', NewsByCategoryView.as_view(), name='get_news_by_category'),
    path('search/', SearchNewsView.as_view(), name='search_news'),
    path('toggle_like/<int:article_id>/', ToggleLikeView.as_view(), name='toggle_like'),
]