from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from itg import settings
from news import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.MainView.as_view(), name='index'),  # Используем MainView для главной страницы
    path('about/', views.AboutView.as_view(), name='about'),  # Используем AboutView для страницы "О проекте"
    path('news/', include('news.urls', namespace='news')),
    # path('users/', include('users.urls', namespace='users')),

    # Общие URL allauth
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns