from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from news.models import Article
from django.views.generic import UpdateView
from django.urls import reverse_lazy

from users.forms import AvatarUploadForm
from users.models import Profile


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'info'
        return context

class MyArticlesView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'users/my_articles.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'articles'
        return context

class ActivityView(LoginRequiredMixin, TemplateView):
    template_name = 'users/activity.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'activity'
        return context

class AvatarUploadView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = AvatarUploadForm
    template_name = 'users/upload_avatar.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user.profile