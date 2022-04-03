from django.contrib import admin

from django_mptt_admin.admin import DjangoMpttAdmin

from pages.models import BusinessDirections, AccessCategories, Specializations, TypeOfPage, Pages
from .models import Post, Category

from mainapp.models import ArticleCategories, Article, ArticleComment, \
    ModeratorNotification, NotificationUsersFromModerator, ModeratorNotificationAboutReModeration \


admin.site.register(ArticleCategories)
admin.site.register(Article)
# admin.site.register(ArticleLike)
admin.site.register(ArticleComment)
admin.site.register(ModeratorNotification)
admin.site.register(NotificationUsersFromModerator)
admin.site.register(ModeratorNotificationAboutReModeration)
admin.site.register(BusinessDirections)
admin.site.register(AccessCategories)
admin.site.register(Specializations)
admin.site.register(TypeOfPage)
admin.site.register(Pages)


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Post, PostAdmin)


class CategoryAdmin(DjangoMpttAdmin):
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Category, CategoryAdmin)
