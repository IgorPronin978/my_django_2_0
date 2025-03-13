from news import views
from django.urls import path
from .views import (
    AllNewsView,
    NewsByCategoryView,
    NewsByTagView,
    SearchNewsView,
    DetailArticleByIdView,
    DetailArticleByTitleView,
    ToggleLikeView,
    ToggleFavoriteView,
    FavoritesView,
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
    path('toggle_favorite/<int:article_id>/', ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('favorites/', FavoritesView.as_view(), name='favorites'),
    path('add/', views.add_article, name='add_article'),
    path('edit/<int:article_id>/', views.article_update, name='article_update'),
    path('delete/<int:article_id>/', views.article_delete, name='article_delete'),
    path('upload_json/', views.upload_json_view, name='upload_json'),
    path('edit_article_from_json/<int:index>/', views.edit_article_from_json, name='edit_article_from_json'),
]