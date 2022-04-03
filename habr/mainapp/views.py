import re

from datetime import timedelta, datetime
from django.utils import timezone

from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse
from django.utils.decorators import method_decorator

from django.views.generic import ListView, DetailView, CreateView, View, RedirectView, \
    UpdateView, TemplateView, DeleteView
from django.shortcuts import HttpResponseRedirect, render, get_object_or_404
from django.http import Http404

from uuid import UUID

from authapp.forms import UserRegisterForm

from mainapp.forms import UserProfileEditForm, UserProfileForm, ModeratorNotificationEditForm, \
    ModeratorNotificationAboutReModerationEditForm, ArticleStatusEditForm, MessageEditForm, \
    FilterForm, GeneralMessageEditForm, ReplyCommentForm

from mainapp.forms import ArticleEditForm, CreationCommentForm, SearchForm
from authapp.models import User, UserProfile
from mainapp.models import Article, ArticleCategories, ArticleComment, ModeratorNotification, \
    ModeratorNotificationAboutReModeration, NotificationUsersFromModerator, \
    NotificationUserAfterLikeAndComment

"""обозначение списка категорий для вывода в меню во разных view"""
category_list = ArticleCategories.objects.all()

"""обозначение формы поиска для вывода в меню во разных view"""
search_form = SearchForm()


def get_sort_from_request(self):
    """метод получения параметра сортировки"""
    try:
        sort = self.request.GET['sort']
        return sort
    except Exception:
        return None


def get_filter_params_from_get_request(self):
    """метод получения параметра сортировки"""
    param_string = ''
    for key, value in self.request.GET.items():
        if key != 'page' and key != 'sort':
            param_string += f'{key}={value}&'
    return param_string.rstrip('&')


def add_filter_params_to_context(self, context):
    for key, value in self.request.GET.items():
        if key != 'page' and key != 'sort' and key != 'query':
            context[key] = value
    try:
        context['start_date'] = datetime.strptime((context['start_date']), "%Y-%m-%d")
        context['end_date'] = datetime.strptime((context['end_date']), "%Y-%m-%d")
    except:
        pass
    return context


def get_filter_article_queryset(self, article_queryset):
    """метод получения отфильтрованных статей"""
    form = FilterForm(self.request.GET)
    if form.is_valid():
        data = form.cleaned_data
    else:
        raise Http404()
    queryset = article_queryset.filter(status='A').exclude(
        blocked='True')
    if data['start_date']:
        queryset = queryset.filter(created_timestamp__gte=data['start_date'])
    if data['end_date']:
        queryset = queryset.filter(created_timestamp__lte=data['end_date'] + timedelta(days=1))
    if data['start_rating']:
        queryset = queryset.filter(article_rating__rating__gte=data['start_rating'])
    if data['end_rating']:
        queryset = queryset.filter(article_rating__rating__lte=data['end_rating'])
    return queryset


def get_sort_article_queryset(self, article_queryset):
    """метод получения сортированных статей"""
    sort = self.get_sort_from_request()
    if sort == 'date_reverse':
        return article_queryset.reverse()
    elif sort == 'rating':
        return article_queryset.order_by(
            'article_rating__rating').reverse()
    elif sort == 'rating_reverse':
        return article_queryset.order_by('article_rating__rating')
    else:
        return article_queryset


class MainListView(ListView):
    """Класс для вывода списка «Хабров» на главной """
    template_name = 'mainapp/index.html'
    paginate_by = 9
    model = Article

    def get_sort_from_request(self):
        return get_sort_from_request(self)

    def get_sort_article_queryset(self, article_queryset):
        return get_sort_article_queryset(self, article_queryset)

    def get_filter_params_from_get_request(self):
        return get_filter_params_from_get_request(self)

    def get_filter_article_queryset(self, article_queryset):
        return get_filter_article_queryset(self, article_queryset)

    def add_filter_params_to_context(self, context):
        return add_filter_params_to_context(self, context)

    def get_queryset(self):
        queryset = Article.objects
        queryset = self.get_filter_article_queryset(queryset)
        queryset = self.get_sort_article_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        # вызов базовой реализации для получения контекста
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная'

        # добавляем в набор запросов все категории
        context['categories_list'] = category_list
        context['search_form'] = search_form

        # добавляем параметры
        context['params'] = self.get_filter_params_from_get_request()
        context['sort'] = self.get_sort_from_request()
        self.add_filter_params_to_context(context)
        return context


class ArticleDetailView(DetailView):
    """Класс для вывода страницы статьи и подборок «Хабров» """
    template_name = 'mainapp/article_page.html'
    model = Article

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Статья'
        context['title'] = title
        context['form'] = CreationCommentForm()
        context['categories_list'] = category_list
        context['search_form'] = search_form
        return context

    def dispatch(self, request, *args, **kwargs):
        article_id = self.kwargs['pk']
        article_status = Article.objects.get(id=article_id).status
        article_blocked = Article.objects.get(id=article_id).blocked
        if article_status != 'A' or article_blocked:
            self.template_name = 'mainapp/404.html'
        return super().dispatch(request, *args, **kwargs)


class CategoriesListView(ListView):
    """Класс для вывода списка категорий """
    template_name = 'mainapp/categories.html'
    paginate_by = 9
    model = Article

    def get_sort_from_request(self):
        return get_sort_from_request(self)

    def get_sort_article_queryset(self, article_queryset):
        return get_sort_article_queryset(self, article_queryset)

    def get_filter_params_from_get_request(self):
        return get_filter_params_from_get_request(self)

    def get_filter_article_queryset(self, article_queryset):
        return get_filter_article_queryset(self, article_queryset)

    def add_filter_params_to_context(self, context):
        return add_filter_params_to_context(self, context)

    def get_queryset(self):
        categories = self.kwargs['pk']
        try:
            UUID(categories)
        except:
            raise Http404()

        queryset = Article.objects.filter(categories_id=categories)
        queryset = self.get_filter_article_queryset(queryset)
        queryset = self.get_sort_article_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        # вызов базовой реализации для получения контекста
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs['pk']
        category = ArticleCategories.objects.get(id=category_id)
        context['title'] = f'Статьи по категории «{category.name}»'
        context['categories_list'] = category_list
        context['categories_pk'] = UUID(category_id)
        context['category_name'] = category.name
        context['search_form'] = search_form

        # добавляем параметры
        context['params'] = self.get_filter_params_from_get_request()
        context['sort'] = self.get_sort_from_request()
        self.add_filter_params_to_context(context)
        return context


class LkListView(ListView):
    """Класс для вывода страницы ЛК """
    template_name = 'mainapp/user_lk.html'
    model = ModeratorNotification

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Личный кабинет'
        re_moderation_notifications_list = ModeratorNotificationAboutReModeration.objects.exclude(
            status='R'
        )
        context['title'] = title
        context['categories_list'] = category_list
        context['re_moderation_notifications_list'] = re_moderation_notifications_list
        return context

    @method_decorator(user_passes_test(lambda u: u.is_active))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CreateArticle(CreateView):
    """Класс для создания статьи"""
    model = Article
    template_name = 'mainapp/updateArticle.html'
    form_class = ArticleEditForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Добавление статьи'
        context['title'] = title
        context['categories_list'] = category_list
        return context

    def get_success_url(self):
        return reverse_lazy('my_articles', args=[self.request.user.id])


class UpdateArticle(UpdateView):
    """Класс для создания статьи"""
    model = Article
    template_name = 'mainapp/updateArticle.html'
    form_class = ArticleEditForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Редактирование статьи'
        context['title'] = title
        context['categories_list'] = category_list
        return context

    def get_success_url(self):
        return reverse_lazy('my_articles', args=[self.request.user.id])

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        article_id = self.kwargs['pk']
        user_id = Article.objects.get(id=article_id).user.id
        if user_id != self.request.user.id:
            self.template_name = 'mainapp/404.html'
        return super(UpdateArticle, self).dispatch(*args, **kwargs)


class ProfileCreateView(CreateView):
    model = UserProfile
    template_name = 'mainapp/updateProfile.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Заполнение профиля'
        context['title'] = title
        context['categories_list'] = category_list
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileCreateView, self).dispatch(*args, **kwargs)


class ProfileEditView(UpdateView):
    model = UserProfile
    template_name = 'mainapp/updateProfile.html'
    form_class = UserProfileEditForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Редактирование профиля'
        context['title'] = title
        context['categories_list'] = category_list
        return context

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileEditView, self).dispatch(*args, **kwargs)


class LkEditView(UpdateView):
    """Класс для вывода страницы ЛК """
    model = UserProfileEditForm
    template_name = 'mainapp/user_lk_update.html'

    @staticmethod
    def post(request, **kwargs):
        title = 'Редактирование ЛК'
        if request.POST:
            edit_user_form = UserRegisterForm(request.POST, request.FILES, instance=request.user)
            profile_form = UserProfileEditForm(request.POST, instance=request.user.userprofile)
            if edit_user_form.is_valid() and profile_form.is_valid():
                edit_user_form.save()
                profile_form.save()
                return HttpResponseRedirect(reverse('lk'))
        else:
            edit_user_form = UserRegisterForm(instance=request.user)
            profile_form = UserProfileEditForm(instance=request.user.userprofile)
            return HttpResponseRedirect(reverse('lk'))

        content = {'title': title, 'edit_user_form': edit_user_form, 'profile_form': profile_form}
        return render(request, LkEditView.template_name, content)


class CreateCommentView(View):
    """Класс для создания комментария """

    @staticmethod
    def post(request):
        article_id = request.POST['article_comment']
        form = CreationCommentForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('article', kwargs={'pk': article_id}))
        else:
            return HttpResponseRedirect(reverse('article', kwargs={'pk': article_id}))


class UserArticleListView(ListView):
    """Класс для вывода списка статей автора"""
    template_name = 'mainapp/article_by_author.html'
    paginate_by = 9
    model = Article

    def get_sort_from_request(self):
        return get_sort_from_request(self)

    def get_sort_article_queryset(self, article_queryset):
        return get_sort_article_queryset(self, article_queryset)

    def get_filter_params_from_get_request(self):
        return get_filter_params_from_get_request(self)

    def get_filter_article_queryset(self, article_queryset):
        return get_filter_article_queryset(self, article_queryset)

    def add_filter_params_to_context(self, context):
        return add_filter_params_to_context(self, context)

    def get_queryset(self):
        user_id = self.kwargs['pk']
        try:
            UUID(user_id)
        except:
            raise Http404()

        queryset = Article.objects.filter(user=user_id)
        queryset = self.get_filter_article_queryset(queryset)
        queryset = self.get_sort_article_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        # вызов базовой реализации для получения контекста
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs['pk']
        author = User.objects.get(id=user_id)
        try:
            context['title'] = f'Статьи автора {author.get_profile().name}'
        except:
            context['title'] = f'Статьи автора {author.username}'
        context['categories_list'] = category_list
        context['author'] = author
        context['search_form'] = search_form
        # добавляем параметры
        context['params'] = self.get_filter_params_from_get_request()
        context['sort'] = self.get_sort_from_request()
        self.add_filter_params_to_context(context)
        return context


class MyArticleListView(ListView):
    """Класс для вывода списка статей автора"""
    template_name = 'mainapp/myArticles.html'
    paginate_by = 9
    model = Article

    def get_queryset(self):
        # Объявляем переменную user и записываем ссылку на id автора
        user_id = self.kwargs['pk']
        new_context = Article.objects.filter(user=user_id).exclude(status='H')
        return new_context

    def get_context_data(self, **kwargs):
        # вызов базовой реализации для получения контекста
        context = super().get_context_data(**kwargs)
        context['categories_list'] = category_list
        context['title'] = f'Мои статьи'
        return context


class SearchView(ListView):
    template_name = 'mainapp/search.html'
    paginate_by = 9
    model = Article

    def get_sort_from_request(self):
        return get_sort_from_request(self)

    def get_sort_article_queryset(self, article_queryset):
        return get_sort_article_queryset(self, article_queryset)

    def get_filter_params_from_get_request(self):
        return get_filter_params_from_get_request(self)

    def get_filter_article_queryset(self, article_queryset):
        return get_filter_article_queryset(self, article_queryset)

    def add_filter_params_to_context(self, context):
        return add_filter_params_to_context(self, context)

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query_string = form.cleaned_data['query']

        queryset = Article.objects.search(query=query_string)
        queryset = self.get_filter_article_queryset(queryset)
        queryset = self.get_sort_article_queryset(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = search_form
        context['categories_list'] = category_list
        context['title'] = 'Поиск по сайту'
        context['query'] = self.request.GET['query']
        # добавляем параметры
        context['params'] = self.get_filter_params_from_get_request()
        context['sort'] = self.get_sort_from_request()
        self.add_filter_params_to_context(context)
        return context


class ArticleLikeRedirectView(RedirectView):
    """Класс для постановки лайка статье"""

    def get_redirect_url(self, *args, **kwargs):
        article_id = self.kwargs.get('pk')
        obj_article = get_object_or_404(Article, id=article_id)
        url_article = obj_article.get_absolute_url()
        user = self.request.user

        if user.is_authenticated and not user.is_now_banned:
            if user in obj_article.likes.all():
                obj_article.likes.remove(user)
            else:
                obj_article.likes.add(user)
        else:
            pass
        return url_article


class CommentLikeRedirectView(RedirectView):
    """Класс для постановки лайка комменту"""

    def get_redirect_url(self, *args, **kwargs):
        obj_article = get_object_or_404(Article, id=self.kwargs['pk'])
        url_article = obj_article.get_absolute_url()
        user = self.request.user

        obj_comment = get_object_or_404(ArticleComment, id=self.kwargs['id'])
        if user.is_authenticated and not user.is_now_banned:
            if user in obj_comment.likes.all():
                obj_comment.likes.remove(user)
            else:
                obj_comment.likes.add(user)
        else:
            pass
        return url_article


class AuthorStarRedirectView(RedirectView):
    """Класс для постановки звезды(лайка) автору статьи"""

    def get_redirect_url(self, *args, **kwargs):
        obj_article = get_object_or_404(Article, id=self.kwargs['pk'])
        url_article = obj_article.get_absolute_url()
        user = self.request.user

        obj_userprofile = get_object_or_404(UserProfile, user_id=obj_article.user_id)
        if user.is_authenticated and not user.is_now_banned:
            if user in obj_userprofile.stars.all():
                obj_userprofile.stars.remove(user)
            else:
                obj_userprofile.stars.add(user)
        else:
            pass
        return url_article


class AuthorArticleStarRedirectView(RedirectView):
    """Класс для постановки звезды(лайка) автору статьи"""

    def get_redirect_url(self, *args, **kwargs):
        user_id = self.kwargs['pk']
        obj_author = get_object_or_404(User, id=user_id)
        url_author_article = obj_author.get_absolute_url()
        user = self.request.user

        obj_userprofile = get_object_or_404(UserProfile, user_id=obj_author.id)
        if user.is_authenticated and not user.is_now_banned:
            if user in obj_userprofile.stars.all():
                obj_userprofile.stars.remove(user)
            else:
                obj_userprofile.stars.add(user)
        else:
            pass
        return url_author_article


class ModeratorNotificationUpdate(UpdateView):
    model = ModeratorNotification
    template_name = 'mainapp/updateModerNotif.html'
    form_class = ModeratorNotificationEditForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Вы действительно хотите взять на модерацию статью?'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class ModeratorNotificationAboutReModerationUpdate(UpdateView):
    model = ModeratorNotificationAboutReModeration
    template_name = 'mainapp/updateModerNotifAboutReModer.html'
    form_class = ModeratorNotificationAboutReModerationEditForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Модерация статьи после доработки автором'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class NotificationUsersAboutBlockingUpdate(UpdateView):
    model = NotificationUsersFromModerator
    template_name = 'mainapp/updateMessage.html'
    form_class = MessageEditForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Вы действительно хотите скрыть сообщение?'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class BannedAuthorCommentView(RedirectView):
    """Класс для блокировки пользователя (автора комментария) на 2 недели"""

    def get_redirect_url(self, *args, **kwargs):
        obj_article = get_object_or_404(Article, id=self.kwargs['pk'])
        url_article = obj_article.get_absolute_url()
        user = self.request.user

        obj_comment = get_object_or_404(ArticleComment, id=self.kwargs['id'])
        if user.is_authenticated and user.is_staff is True:
            banned_date = timezone.now() + timedelta(days=14)
            obj_comment.user.date_end_banned = banned_date
            obj_comment.user.save()
        else:
            pass
        return url_article


class BannedAuthorArticleView(RedirectView):
    """Класс для блокировки пользователя (автора статьи) на 2 недели"""

    def get_redirect_url(self, *args, **kwargs):
        obj_article = get_object_or_404(Article, id=self.kwargs['pk'])
        url_article = obj_article.get_absolute_url()
        user = self.request.user

        obj_userprofile = get_object_or_404(UserProfile, user_id=obj_article.user_id)
        if user.is_authenticated and user.is_staff is True:
            banned_date = timezone.localtime(timezone.now()) + timedelta(days=14)
            obj_userprofile.user.date_end_banned = banned_date
            obj_userprofile.user.save()
        else:
            pass
        return url_article


class ArticleStatusUpdate(UpdateView):
    template_name = 'mainapp/myArticles.html'
    paginate_by = 9
    model = Article
    form_class = ArticleStatusEditForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои статьи'
        context['categories_list'] = category_list
        return context

    def get_success_url(self):
        if re.search(r'\/article\/', self.request.META.get('HTTP_REFERER')):
            return reverse_lazy('main')
        elif re.search(r'\/ModerNotReMod-update\/', self.request.META.get('HTTP_REFERER')):
            return reverse_lazy('lk')
        else:
            return reverse_lazy('my_articles', args=[self.request.user.id])


class PageNotFountView(TemplateView):
    template_name = "mainapp/404.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Страница не найдена'
        context['categories_list'] = category_list
        return context


class UserCommentDeleteView(DeleteView):
    model = ArticleComment

    def get_success_url(self):
        article_id = self.request.META['HTTP_REFERER'].split('/')[-2]
        return reverse_lazy('article', kwargs={'pk': article_id})

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class ModeratorNotificationReviewedUpdate(UpdateView):
    """Снятие модератором статьи с модерации"""
    model = ModeratorNotification
    template_name = 'mainapp/updateModerNotifReviewed.html'
    form_class = ModeratorNotificationEditForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Вы действительно хотите снять с модерации статью?'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class GeneralNotificationUsersUpdate(UpdateView):
    """Переместить уведомление в прочитанные"""
    model = NotificationUserAfterLikeAndComment
    template_name = 'mainapp/updateGeneralMessage.html'
    form_class = GeneralMessageEditForm
    success_url = reverse_lazy('lk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Переместить уведомление в прочитанные?'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class AllGeneralNotificationUserView(ListView):
    """Подтверждение о перемещении всех уведомлений в прочитанные"""
    model = NotificationUserAfterLikeAndComment
    template_name = 'mainapp/updateAllGeneralMessage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = 'Переместить все уведомления в прочитанные?'
        context['title'] = title
        context['categories_list'] = category_list
        return context


class AllGeneralNotificationUserUpdate(RedirectView):
    """Переместить все уведомления в прочитанные"""

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        obj_notify = user.get_general_user_notification()
        for gen_notify in obj_notify:
            gen_notify.is_read = True
            gen_notify.save()
        return reverse_lazy('lk')


class ReplyCommentView(View):
    """Класс для создания ответа на комментарий """

    @staticmethod
    def post(request):
        article_id = request.POST['pk']
        form = ReplyCommentForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('article', kwargs={'pk': article_id}))
        else:
            return HttpResponseRedirect(reverse('article', kwargs={'pk': article_id}))
