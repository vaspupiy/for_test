import uuid
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

import mainapp.models as mainapp_models


class BaseModel(models.Model):
    """
    Global model. Set id and created_timestamp for all children models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='id')
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Create Date')

    @classmethod
    def get_item_by_id(cls, search_id):
        return cls.objects.filter(id=search_id)


class User(AbstractUser, BaseModel, PermissionsMixin):
    """
    Model for user`s registration
    """
    username = models.CharField(verbose_name='user_name', unique=True, max_length=25, blank=False)
    email = models.EmailField(verbose_name='email', unique=True, blank=False)
    password = models.CharField(verbose_name='password', max_length=250, blank=False)
    first_name = None
    last_name = None
    is_banned = models.BooleanField(default=False, verbose_name='Заблокирован')
    date_end_banned = models.DateTimeField(null=True, blank=True, default=None)

    def __init__(self, *args, **kwargs):
        """ для фиксации изменений о статусе аккаунта"""
        super(User, self).__init__(*args, **kwargs)
        self.__original_is_banned = self.is_banned
        self.__original_date_end_banned = self.date_end_banned

    def __str__(self):
        return f"{self.username} - {self.userprofile.name}"

    def get_profile(self):
        """
        Метод отдает профиль текущего пользователя
        """
        return UserProfile.objects.filter(user=self).select_related("user").first()

    def get_absolute_url(self):
        """
        Метод отдает абсолютную ссылку на страницу статей автора
        """
        return reverse("user_article", kwargs={"pk": self.id})

    def get_count_notifications_on_moderation(self):
        return mainapp_models.ModeratorNotification.objects.filter(
            responsible_moderator=self
        ).exclude(
            status='R'
        ).count()

    def get_count_notifications_on_article_for_re_moderation(self):
        return mainapp_models.ModeratorNotificationAboutReModeration.objects.filter(
            responsible_moderator=self
        ).exclude(
            status='R'
        ).count()

    @property
    def is_now_banned(self) -> bool:
        if self.is_banned:
            return True
        if self.date_end_banned and self.date_end_banned > timezone.now():
            return True
        return False

    def get_notification_about_blocking(self):
        return mainapp_models.NotificationUsersFromModerator.objects.filter(
            recipient_notification=self
        ).exclude(
            is_read=True
        ).select_related(
            "recipient_notification"
        ).order_by(
            '-created_timestamp'
        )

    def get_count_notifications_about_blocking(self):
        return mainapp_models.NotificationUsersFromModerator.objects.filter(
            recipient_notification=self
        ).exclude(
            is_read=True
        ).select_related(
            "recipient_notification"
        ).count()

    def get_general_user_notification(self):
        return mainapp_models.NotificationUserAfterLikeAndComment.objects.filter(recipient_notification=self). \
            exclude(is_read=True).select_related("recipient_notification").order_by('-created_timestamp')

    def get_count_general_user_notification(self):
        return mainapp_models.NotificationUserAfterLikeAndComment.objects.filter(recipient_notification=self). \
            exclude(is_read=True).select_related("recipient_notification").count()


class UserProfile(models.Model):
    """
    Model for users
    """
    user = models.OneToOneField(User, unique=True, null=False, db_index=True, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Имя Фамилия', max_length=100, blank=False)
    birthday = models.DateField(verbose_name='День рождения', null=True, blank=True)
    bio = models.TextField(verbose_name='Краткое описание', max_length=120, blank=False)
    avatar = models.ImageField(verbose_name='Аватар', upload_to='user_avatars')
    stars = models.ManyToManyField(User, blank=True, related_name='author_stars')
    rating = models.PositiveIntegerField(default=0, verbose_name='author_rating')
    previous_article_rating = models.PositiveIntegerField(default=0, verbose_name='article_previous_rating')

    def __str__(self):
        return f'Userprofile for "{self.user.username}"'

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, update_fields, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.userprofile.save()


@receiver(m2m_changed, sender=UserProfile.stars.through)
def change_author_rating_by_author_likes(sender, instance, action, **kwargs):
    """
    Сигнал для изменения рейтинга автора от изменения лайков этому автору
    """
    if action == 'post_add':
        instance.rating += 1
        instance.save()

    if action == 'post_remove' and instance.rating != 0:
        instance.rating -= 1
        instance.save()
