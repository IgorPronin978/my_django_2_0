from django.urls import path
from .views import ProfileView, MyArticlesView, ActivityView, AvatarUploadView

app_name = 'users'

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/articles/', MyArticlesView.as_view(), name='my_articles'),
    path('profile/activity/', ActivityView.as_view(), name='activity'),
    path('profile/upload-avatar/', AvatarUploadView.as_view(), name='upload_avatar'),
]