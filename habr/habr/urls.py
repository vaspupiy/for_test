from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.decorators.cache import never_cache

from mainapp.views import MainListView, ArticleDetailView, \
    CategoriesListView, UserArticleListView, CreateCommentView, CreateArticle, SearchView, \
    ArticleLikeRedirectView, CommentLikeRedirectView, \
    AuthorStarRedirectView, AuthorArticleStarRedirectView, UpdateArticle, ProfileCreateView, \
    ProfileEditView, LkListView, MyArticleListView, BannedAuthorCommentView, BannedAuthorArticleView, \
    ModeratorNotificationUpdate, NotificationUsersAboutBlockingUpdate, PageNotFountView, \
    ModeratorNotificationAboutReModerationUpdate, \
    ArticleStatusUpdate, UserCommentDeleteView, ModeratorNotificationReviewedUpdate, GeneralNotificationUsersUpdate, \
    AllGeneralNotificationUserView, AllGeneralNotificationUserUpdate, ReplyCommentView

from qrgenerator.views import index as qr

from authapp.views import UserEditView
from ckeditor_uploader import views

urlpatterns = [

    path('', MainListView.as_view(), name='main'),
    path('lk/', LkListView.as_view(), name='lk'),
    path('lk/add/', ProfileCreateView.as_view(), name='profile_add'),
    path('lk/edit/<str:pk>/', ProfileEditView.as_view(), name='profile_edit'),
    path('lk/read-block-message/<str:pk>/', NotificationUsersAboutBlockingUpdate.as_view(), name='message_edit'),
    path('lk/read-general-message/<str:pk>/', GeneralNotificationUsersUpdate.as_view(), name='gen_message_edit'),
    path('article/<str:pk>/', ArticleDetailView.as_view(), name='article'),
    path('user-edit/<str:pk>/', UserEditView.as_view(), name='user_edit'),
    path('article-add/', CreateArticle.as_view(), name='article_create'),
    path('article-update/<str:pk>/', UpdateArticle.as_view(), name='article_update'),

    path('ModerNot-update/<str:pk>/', ModeratorNotificationUpdate.as_view(), name='moder_not_update'),

    path('ModerNotReMod-update/<str:pk>/',
         ModeratorNotificationAboutReModerationUpdate.as_view(),
         name='moder_not_re_mod_update'),

    path('ModerNotRev-update/<str:pk>/', ModeratorNotificationReviewedUpdate.as_view(), name='moder_not_rev_update'),


    path('add-comment/', CreateCommentView.as_view(), name='add-comment'),
    path('reply-comment/', ReplyCommentView.as_view(), name='reply-comment'),
    path('category/<str:pk>/', CategoriesListView.as_view(), name='category'),
    path('user-article/<str:pk>/', UserArticleListView.as_view(), name='user_article'),
    path('my-articles/<str:pk>/', MyArticleListView.as_view(), name='my_articles'),
    path('accounts/', include('authapp.urls', namespace='auth')),

    path('ckeditor/upload/', login_required(views.upload), name='ckeditor_upload'),
    path('ckeditor/browse/', never_cache(login_required(views.browse)), name="ckeditor_browse"),

    path('search/', SearchView.as_view(), name='search'),
    path('admin/', admin.site.urls),

    path('article/<str:pk>/like/', ArticleLikeRedirectView.as_view(), name='like-toggle'),
    path('article/<str:pk>/star/', AuthorStarRedirectView.as_view(), name='star_toggle'),
    path('article/<str:pk>/like/<str:id>', CommentLikeRedirectView.as_view(), name='like_comment_toggle'),
    path('user-article/<str:pk>/star/', AuthorArticleStarRedirectView.as_view(), name='user_article_star_toggle'),

    path('article/<str:pk>/banned/<str:id>', BannedAuthorCommentView.as_view(), name='banned_user_toggle'),
    path('article/<str:pk>/banned/', BannedAuthorArticleView.as_view(), name='banned_author_article_toggle'),
    path('status-update/<str:pk>/', ArticleStatusUpdate.as_view(), name='article_status_update'),
    path('article/<str:pk>/banned/', BannedAuthorArticleView.as_view(), name='banned_author_article_toggle'),
    path('user-comment-delete/<str:pk>/', UserCommentDeleteView.as_view(), name='comment_delete'),

    path('warning-all-gen-notify/<str:pk>/', AllGeneralNotificationUserView.as_view(), name='warning_all_gen_notify'),
    path('update-all-gen-notify/<str:pk>/', AllGeneralNotificationUserUpdate.as_view(), name='update_all_gen_notify'),
    path('qr/', qr, name='qr-generator')
]

handler404 = PageNotFountView.as_view()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
