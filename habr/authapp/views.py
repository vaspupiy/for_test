from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from authapp.forms import UserRegisterForm, UserLoginForm
from authapp.models import User
from mainapp.models import ArticleCategories

"""обозначение списка категорий для вывода в меню во разных view"""
category_list = ArticleCategories.objects.all()


class UserRegistrationView(CreateView):
    model = User
    template_name = 'authapp/registration.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('auth:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Регистрация'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class UserEditView(UpdateView):
    model = User
    template_name = 'authapp/user_edit.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('auth:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Изменение учётных данных'
        context['title'] = title
        context['categories_list'] = category_list
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserEditView, self).dispatch(*args, **kwargs)


class UserLoginView(LoginView):
    template_name = 'authapp/authorization.html'
    form_class = UserLoginForm
    next_page = reverse_lazy('main')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторизация'
        context['categories_list'] = category_list
        return context


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('auth:login')
