from django.urls import path
from . import views


# будет иметь префикс в urlах /news/
urlpatterns = [
    path('catalog/', views.get_all_news),
    path('catalog/', views.catalog, name='catalog'),
    path('catalog/<int:article_id>/', views.get_detail_article_by_id, name='detail_article_by_id'),
    path('catalog/<slug:slug>/', views.category_by_name),
]