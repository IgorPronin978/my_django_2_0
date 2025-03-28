from allauth.account.views import ConfirmEmailView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView

from .forms import CustomAuthenticationForm
from news.views import MenuMixin


class LogoutUser(MenuMixin, LogoutView):
    next_page = reverse_lazy('account_login')


class RegisterDoneView(LoginRequiredMixin, MenuMixin, TemplateView):
    template_name = 'users/register_done.html'
    extra_context = {'title': 'Регистрация завершена'}


class CustomConfirmEmailView(ConfirmEmailView):
    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        if self.object.emailaddress_set.filter(verified=True).exists():
            return redirect('account_login')
        return response