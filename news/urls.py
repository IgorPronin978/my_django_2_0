from django.urls import path
from . import views

app_name = 'news'
urlpatterns = [
    path('catalog/', views.AllNewsView.as_view(), name='catalog'),
    path('catalog/<int:article_id>/', views.ArticleDetailView.as_view(), name='detail_article_by_id'),
    path('catalog/<slug:title>/', views.ArticleDetailView.as_view(), name='detail_article_by_title'),
    path('tag/<int:tag_id>/', views.NewsByTagView.as_view(), name='get_news_by_tag'),
    path('category/<int:category_id>/', views.NewsByCategoryView.as_view(), name='get_news_by_category'),
    path('search/', views.SearchNewsView.as_view(), name='search_news'),
    path('toggle_like/<int:article_id>/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('toggle_favorite/<int:article_id>/', views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('favorites/', views.FavoritesView.as_view(), name='favorites'),
    path('add/', views.AddArticleView.as_view(), name='add_article'),
    path('edit/<int:pk>/', views.ArticleUpdateView.as_view(), name='article_update'),
    path('delete/<int:pk>/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('upload_json/', views.UploadJsonView.as_view(), name='upload_json'),
    path('edit_article_from_json/<int:index>/', views.EditArticleFromJsonView.as_view(), name='edit_article_from_json'),
    path('subscribe/author/<int:author_id>/',  # POST
          views.ToggleAuthorSubscriptionView.as_view(),
          name='toggle_author_subscription'),
     path('subscribe/tag/<int:tag_id>/',        # POST
          views.ToggleTagSubscriptionView.as_view(),
          name='toggle_tag_subscription'),
]