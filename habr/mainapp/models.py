import inspect
import uuid
import re

from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.db.models.query import QuerySet
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.db.models import Avg
from django.utils import timezone
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase, Tag

from authapp.models import User, UserProfile
from mainapp.manager import ArticleManager


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    tag = models.ForeignKey(Tag, related_name="uuid_tagged_items", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"


class BaseModel(models.Model):
    """
    Global model. Set id and created_timestamp for all children models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name='id')
    created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Create Date')

    @classmethod
    def get_item_by_id(cls, search_id):
        return cls.objects.filter(id=search_id)


class ArticleCategories(BaseModel):
    """
    Models for Article Categories
    """
    name = models.CharField(max_length=32, unique=True, verbose_name='name categories')
    is_active = models.BooleanField(default=True, verbose_name='active')

    def __str__(self):
        return self.name


class Article(BaseModel):
    """
    Models for Articles
    """
    # добавили менеджер для изменения логики поиска в модели
    objects = ArticleManager()

    DRAFT = 'D'
    ACTIVE = 'A'
    ARCHIVE = 'H'

    STATUS_CHOICES = (
        (DRAFT, 'Черновик'),
        (ACTIVE, 'Активная'),
        (ARCHIVE, 'Архивная'),
    )

    categories = models.ForeignKey(ArticleCategories, on_delete=models.CASCADE, verbose_name='categories')
    title = models.CharField(max_length=60, verbose_name='title')
    subtitle = models.CharField(max_length=100, verbose_name='subtitle')
    main_img = models.ImageField(upload_to='article_images', verbose_name='img')
    text = RichTextUploadingField(config_name='awesome_ckeditor')
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name='Author article',
                             related_name='article_author')
    likes = models.ManyToManyField(User, blank=True, related_name='post_likes')
    tags = TaggableManager(through=UUIDTaggedItem)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, verbose_name='Статус', default='D')
    blocked = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        """ для фиксации изменений о статусе аккаунта"""
        super(Article, self).__init__(*args, **kwargs)
        self.__original_status = self.status
        self.__original_blocked = self.blocked

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'article'
        ordering = ['-created_timestamp']

    @classmethod
    def get_all_articles(cls) -> QuerySet:
        """
        :param: None
        :return: QuerySet with all Articles in DataBase

        Method for get QuerySet with all ARTICLES in DataBase.
        Method called from Classes.
        All article sorted by date descending order.
        """
        return Article.objects.all()

    @classmethod
    def get_all_articles_in_pagination(cls, pagination_page: int) -> Paginator:
        """
        :param: desired count page in pagination
        :return: QuerySet with all ARTICLES in DataBase in Pagination object

          Method called from Classes.
          All article sorted by date descending order.
          """
        all_articles: QuerySet = cls.get_all_articles()
        pagination_articles: Paginator = Paginator(all_articles, pagination_page)
        return pagination_articles

    def get_comment_count_by_article_id(self) -> int:
        """
        Подсчет количества комментариев для статьи.
        """
        return ArticleComment.objects.select_related('article_comment').filter(article_comment=self.id).count()

    def get_comments_by_article_id(self) -> QuerySet:
        """
        :param: None
        :return: QuerySet with all COMMENTS in DataBase by specific Article.

          Method called from Article Item.
          All likes sorted by date descending order.
          """
        return ArticleComment.objects.select_related('article_comment').filter(article_comment=self.id)

    def get_other_articles_by_author(self) -> QuerySet:
        """
        Метод выводит последние по дате 3 статьи автора исключая текущую статью
          """
        return Article.objects.filter(user=self.user, status='A').exclude(id=self.id).order_by('-created_timestamp')[:3]

    def get_absolute_url(self):
        """
        Метод отдает абсолютную ссылку на страницу статьи
        """
        return reverse("article", kwargs={"pk": self.id})

    def get_article_text_preview(self):
        """
        Метод выводит первые 250 символов текста статьи
        """
        preview = re.sub(r'\<[^>]*\>', '', self.text)
        return f'{preview[:250]}.....'

    def get_like_url(self):
        """
        Метод отдает ссылку по которой статья получает лайк
        """
        return reverse("like-toggle", kwargs={"pk": self.id})

    def get_like_api_url(self):
        """
        Метод отдает ссылку для перехода в api rest_framework
        """
        return reverse("like-api-toggle", kwargs={"pk": self.id})

    def get_rating_by_article_id(self) -> QuerySet:
        """
        Получение рейтинга для статьи.
        """
        return ArticleRating.objects.get(article_rating=self.id).rating

    @property
    def is_for_correction(self) -> bool:
        if self.status == 'D' and self.blocked:
            return True
        return False

    @property
    def is_for_re_moderation(self) -> bool:
        if self.status == 'A' and self.blocked:
            return True
        return False


# сигнал для создания таблицы рейтинга к статье
@receiver(post_save, sender=Article)
def create_article_rating(instance, created, **kwargs):
    if created:
        new_rating = ArticleRating()
        new_rating.article_rating = instance
        new_rating.article_author = instance.user
        new_rating.save()
        return None


class ArticleComment(BaseModel):
    """
    Models for Articles Comments
    """
    article_comment = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='Article for comment',
                                        related_name='article_comment')
    text = models.TextField(max_length=300, verbose_name='Comment text')
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name='Comment Author',
                             related_name='comment_author')
    likes = models.ManyToManyField(User, blank=True, related_name='comment_likes')

    def __str__(self):
        return f'from "{self.user.username}" for "{self.article_comment.title}"'

    class Meta:
        db_table = 'article_comments'
        ordering = ['-created_timestamp']

    def get_replies_by_comment_id(self) -> QuerySet:
        """
        Метод для нахождения ответов на комментарий
        """
        return ReplyComments.objects.select_related('comment_to_reply').filter(comment_to_reply=self)

    def get_count(self):
        """
        метод для подсчета ответов на комментарий
        """
        return ReplyComments.objects.filter(comment_to_reply=self).count()


class ReplyComments(BaseModel):
    """
    Model for Reply on Comments
    """
    comment_to_reply = models.ForeignKey(ArticleComment, on_delete=models.CASCADE, verbose_name='Comment to reply',
                                         related_name='comment_to_reply')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='ReplyComment Author',
                             related_name='reply_comment_author')
    text = models.TextField(max_length=300, verbose_name='ReplyComment Text')

    def __str__(self):
        return f'from {self.user.username} to {self.comment_to_reply.user.username}'

    class Meta:
        ordering = ['-created_timestamp']


class ModeratorNotification(BaseModel):
    """
    Модель для хранения  и уведомления модератора о наличии жалобы на статью
    """

    NEW = 'N'
    ASSIGNED = 'A'
    UNDER_CONSIDERATION = 'U'
    REVIEWED = 'R'

    STATUS_CHOICES = (
        (NEW, 'Новая'),
        (ASSIGNED, 'Назначена'),
        (UNDER_CONSIDERATION, 'На рассмотрении'),
        (REVIEWED, 'Рассмотрена'),
    )

    comment_initiator = models.ForeignKey(
        ArticleComment,
        on_delete=models.CASCADE,
        verbose_name='Comment initiator',
        related_name='comment_initiator'
    )
    responsible_moderator = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        verbose_name='Responsible moderator',
        related_name='responsible_moderator',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        verbose_name='Статус',
        default='N'
    )

    def __str__(self):
        status_verbose_names = {'N': 'Новая',
                                'A': 'Назначена',
                                'U': 'На рассмотрении',
                                'R': 'Рассмотрена'}
        return f'Запрос на проверку статьи "{self.comment_initiator.article_comment}"; ' \
               f'от "{self.comment_initiator.user}"; ' \
               f'статус заявки: {status_verbose_names[self.status]}.'

    class Meta:
        db_table = 'moderator_notification'
        ordering = ['-created_timestamp']

    @staticmethod
    def get_count_new_requests_moderation():
        return ModeratorNotification.objects.filter(status='N').count()

    @receiver(post_save, sender=ArticleComment)
    def create_moderator_notification(sender, instance, **kwargs):
        if '@moderator' in instance.text:
            ModeratorNotification.objects.create(comment_initiator=instance, )


class ArticleRating(BaseModel):
    """
    Models for Articles Rating
    """
    article_rating = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='article_for_rating',
                                       related_name='article_rating')
    rating = models.PositiveSmallIntegerField(default=0, verbose_name='rating')
    article_author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='article_author')

    def __str__(self):
        return f'from article "{self.article_rating.title}" rating = "{self.rating}"'

    class Meta:
        db_table = 'article_rating'
        ordering = ['rating']


@receiver(m2m_changed, sender=ArticleComment.likes.through)
def change_author_rating_by_likes_to_author_comments(sender, instance, action, **kwargs):
    """
    Сигнал для изменения рейтинга автора от изменения лайков к комментариям этого автора
    """

    author = UserProfile.objects.get(user=instance.user.id)

    if action == 'post_add':
        author.rating += 1
        author.save()

    if action == 'post_remove' and author.rating != 0:
        author.rating -= 1
        author.save()


@receiver(post_save, sender=ArticleRating)
@receiver(post_delete, sender=ArticleRating)
def change_author_rating_by_article_rating(sender, instance, **kwargs):
    """
    Сигнал для изменения рейтинга автора от изменения рейтинга статей этого автора
    """
    author = instance.article_rating.user
    instance.article_author = author

    previous_article_rating = author.userprofile.previous_article_rating
    author.userprofile.rating -= previous_article_rating

    rating_objects_by_author = None if not ArticleRating.objects.filter(article_author=author) \
        else ArticleRating.objects.filter(article_author=author)

    if not rating_objects_by_author:
        new_article_rating = instance.rating
    else:
        new_article_rating = rating_objects_by_author.aggregate(avg_duration=Avg('rating'))['avg_duration']

    author.userprofile.rating += int(new_article_rating)
    author.userprofile.previous_article_rating = int(new_article_rating)

    author.save()


@receiver(m2m_changed, sender=Article.likes.through)
def change_article_rating_by_likes_to_article(instance, action, **kwargs):
    """
    Сигнал для изменения рейтинга статьи от изменения кол-ва лайков к статье
    """
    article_rating = ArticleRating.objects.get(article_rating_id=instance.id)
    # ценость одного лайка и одного комментария
    value_one_like = 1
    value_one_comments = 0.2
    if action in ['post_add', 'post_remove']:
        new_article_rating = instance.likes.count() * value_one_like + int(
            instance.get_comment_count_by_article_id() * value_one_comments)
        article_rating.rating = new_article_rating
        article_rating.save()
        return None


@receiver(post_save, sender=ArticleComment)
@receiver(post_delete, sender=ArticleComment)
def change_article_rating_by_count_comments_to_article(instance, **kwargs):
    """
    Сигнал для изменения рейтинга статьи от изменения кол-ва комментов к статье
    """
    article_rating = ArticleRating.objects.get(article_rating_id=instance.article_comment.id)
    # ценость одного лайка и одного комментария
    value_one_like = 1
    value_one_comments = 0.2
    new_article_rating = instance.article_comment.likes.count() * value_one_like + int(
        instance.article_comment.get_comment_count_by_article_id() * value_one_comments)
    article_rating.rating = new_article_rating
    article_rating.save()
    return None


class NotificationUsersFromModerator(BaseModel):
    """
    Уведомление пользователей о блокировки аккаунта,
    а так же о блокировках и удалении контента
    """
    recipient_notification = models.ForeignKey(
        User,
        null=False,
        db_index=True,
        on_delete=models.CASCADE,
        verbose_name='получатель уведомления'
    )

    moderator = models.UUIDField(
        verbose_name='модератор',
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name='прочитано',
    )

    message = models.CharField(
        max_length=500,
        verbose_name='уведомление',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'уведомление о блокировке пользователя "{self.recipient_notification.username}"'

    @staticmethod
    def get_moderator(inspect_stack):
        """получаем модератора из request"""
        for frame_record in inspect_stack:
            if frame_record[3] == 'get_response':
                request = frame_record[0].f_locals['request']
                return request.user
        return

    @staticmethod
    def get_full_message(part_1, part_2):
        """создаем строку сообщения"""
        if part_1 and part_2:
            return f'<p>{part_1}</p><p>{part_2}</p>'
        if part_1:
            return f'<p>{part_1}</p>'
        if part_2:
            return f'<p>{part_2}</p>'

    @receiver(post_save, sender=User)
    def create_moderator_notification(sender, instance, **kwargs):
        """
        При изменении модели User проверяем, изменились ли данные,
        отвечающие за блокировку пользователя. В зависимости от изменений,
        отправляем соответствующие сообщения, если требуется.
        Если изменений не было; если пользователь как был заблокирован
        бессрочно, так и остался; или пользователь как не был заблокирован,
        так и остался не заблокирован - уведомление не создается
        """
        #  получаем составные части сообщения
        part_1, part_2 = '', ''  # все сообщения будут формироваться из этих кусков
        if instance.is_banned != instance._User__original_is_banned:  # было изм. поле is_banned
            if instance.is_banned:  # уст. бессрочный бан
                part_1 = "Ваш аккаунт заблокирован модератором бессрочно."
            else:
                part_1 = "C Вашего аккаунта снята бессрочная блокировка."
                if instance.is_now_banned:  # в настоящий момент действует временный бан
                    part_2 = f'Ваш аккаунт заблокирован модератором до' \
                             f' {instance.date_end_banned.strftime("%d.%m.%Y %H:%M:%S %Z")}.'
        elif not instance.is_banned and \
                instance.date_end_banned != instance._User__original_date_end_banned:
            # было изменение временной блокировки, и нет бессрочного бана
            if instance.is_now_banned:  # временная блокировка действует
                part_1 = f'Ваш аккаунт заблокирован модератором ' \
                         f'до {str(instance.date_end_banned.strftime("%d.%m.%Y %H:%M:%S %Z"))}.'
            elif instance._User__original_date_end_banned \
                    and instance._User__original_date_end_banned > timezone.now():
                # действовал временный бан, но был снят
                part_1 = f'C Вашего аккаунта снята временная блокировка.'
            else:
                return  # если пользователь как не был заблокирован, так и остался не заблокирован
        else:
            return  # если ни чего не менялось или если пользователь как был заблокирован бессрочно, так и остался

        message = NotificationUsersFromModerator.get_full_message(part_1, part_2)
        moderator = NotificationUsersFromModerator.get_moderator(inspect.stack())

        NotificationUsersFromModerator.objects.create(
            recipient_notification=instance,
            moderator=moderator.pk,
            message=message
        )

    @receiver(post_save, sender=Article)
    def create_notification_article_status_update(sender, instance, **kwargs):
        """
        Уведомление пользователя при блокировке статьи модератором
        """

        recipient_notification = instance.user
        moderator = NotificationUsersFromModerator.get_moderator(inspect.stack())

        if recipient_notification == moderator:
            #  Если изменения вносит автор - выходим
            return

        # Получаем значение полей до изменений
        status_before = instance._Article__original_status
        blocked_before = instance._Article__original_blocked

        # Получаем значение полей после изменений
        status = instance.status
        blocked = instance.blocked

        # if not blocked and status_before == status:
        #     #  Если поля status и нет блокировки - выходим
        #     return

        #  получаем составные части сообщения
        part_1, part_2 = '', ''  # все сообщения будут формироваться из этих кусков
        if status_before == 'A' and status == 'D':
            #  Если статус изменился с Активной на Черновик
            if not blocked_before and blocked:
                # если статья была не была заблокирована и ее заблокировали
                part_1 = f'Модератор отправил Вашу статью под заголовком: ' \
                         f' <a class="article-button" ' \
                         f'href="/article-update/{instance.pk}/">' \
                         f'{instance.title} ' \
                         f'</a>' \
                         f' на доработку.'
            elif blocked_before and blocked:
                # если статья была и осталась заблокированной
                part_1 = f'Ваша статья под заголовком: ' \
                         f' <a class="article-button" ' \
                         f'href="/article-update/{instance.pk}/">' \
                         f'{instance.title} ' \
                         f'</a>' \
                         f' не прошла модерацию. <br />' \
                         f'Просим Вас быть внимательнее, ' \
                         f'в следующий раз могут быть приняты более жесткие меры'

        if blocked and status_before != status or not blocked_before and blocked:
            # Если статья заблокирована и менялся статус, или не была заблокирована и ее заблокировали
            part_2 = 'Статья заблокирована для публикации. ' \
                     'Для повторной публикации необходимо исправить статью и ' \
                     'получить разрешение на публикацию от модератора'

        if not blocked and blocked_before:
            # Если статью заблокировали
            part_1 = f'Модератор снял блокировку Вашей стати под заголовком: ' \
                     f'"{instance.title}" ' \
                     f'Вы можете снова опубликовать эту статью.'

        if part_1 or part_2:
            message = NotificationUsersFromModerator.get_full_message(part_1, part_2)
        else:
            return

        NotificationUsersFromModerator.objects.create(
            recipient_notification=recipient_notification,
            moderator=moderator.pk,
            message=message
        )

    @receiver(post_delete, sender=ArticleComment)
    def create_notification_after_delete_comment(sender, instance, **kwargs):
        """
        Уведомление пользователя при удалении комментария модератором
        """
        recipient_notification = instance.user
        moderator = NotificationUsersFromModerator.get_moderator(inspect.stack())
        if len(instance.text) > 60:
            message = f'Модератор удалил Ваш комментарий: {instance.text[:60]}...'
        else:
            message = f'Модератор удалил Ваш комментарий: {instance.text}'

        NotificationUsersFromModerator.objects.create(
            recipient_notification=recipient_notification,
            moderator=moderator.pk,
            message=message
        )


class ModeratorNotificationAboutReModeration(BaseModel):
    """
    Модель для хранения и уведомления модератора о повторной модерации статьи
    """

    NEW = 'N'
    ASSIGNED = 'A'
    UNDER_CONSIDERATION = 'U'
    REVIEWED = 'R'

    STATUS_CHOICES = (
        (NEW, 'Новая'),
        (ASSIGNED, 'Назначена'),
        (UNDER_CONSIDERATION, 'На рассмотрении'),
        (REVIEWED, 'Рассмотрена'),
    )

    article_for_re_moderation = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        verbose_name='Статья для повторной модерации',
        related_name='article_for_re_moderation'
    )
    responsible_moderator = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        verbose_name='Ответственный модератор',
        related_name='responsible_article_moderator',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        verbose_name='Статус',
        default='N'
    )

    def __str__(self):
        status_verbose_names = {'N': 'Новая',
                                'A': 'Назначена',
                                'U': 'На рассмотрении',
                                'R': 'Рассмотрена'}
        return f'Запрос на проверку статьи "{self.article_for_re_moderation}"; ' \
               f'от "{self.article_for_re_moderation.user}"; ' \
               f'статус заявки: {status_verbose_names[self.status]}.'

    class Meta:
        db_table = 'moderator_notification_about_re_moderation'
        ordering = ['-created_timestamp']

    @staticmethod
    def get_user(inspect_stack):
        """получаем модератора из request"""
        for frame_record in inspect_stack:
            if frame_record[3] == 'get_response':
                request = frame_record[0].f_locals['request']
                return request.user
        return

    @receiver(post_save, sender=Article)
    def create_notification_article_status_update(sender, instance, **kwargs):
        """
        Уведомление модератора об отправки статьи автором на модерацию
        """

        author_article = instance.user
        user = ModeratorNotificationAboutReModeration.get_user(inspect.stack())

        if author_article != user:
            #  Если изменения вносит не автор - выходим
            return

        # Получаем значение полей до изменений
        article_status_before = instance._Article__original_status
        article_blocked_before = instance._Article__original_blocked

        # Получаем значение полей после изменений
        article_status = instance.status

        if article_status_before == article_status or not article_blocked_before:
            #  Если поля status не менялись или статья не заблокирована - выходим
            return

        if article_status_before == 'D' and article_status == 'A':
            ModeratorNotificationAboutReModeration.objects.create(
                article_for_re_moderation=instance,
            )

    @staticmethod
    def get_count_new_article_for_re_moderation():
        return ModeratorNotificationAboutReModeration.objects.filter(status='N').count()


class NotificationUserAfterLikeAndComment(BaseModel):
    """
    Уведомления пользователей о лайках статьи, лайках автора и комментариях к статье
    """
    recipient_notification = models.ForeignKey(User, null=False, db_index=True, on_delete=models.CASCADE,
                                               verbose_name='получатель уведомления')
    sender_notification = models.UUIDField(verbose_name='отправитель уведомления')
    is_read = models.BooleanField(default=False, verbose_name='прочитано')
    message = models.CharField(max_length=200, verbose_name='уведомление', blank=True, null=True)

    def __str__(self):
        return f'уведомление пользователя "{self.recipient_notification.username} о лайке или комменте"'

    def get_user_sender(self):
        """
        Метод отдает пользователя, который стал инициатором создания уведомления
        """
        return User.objects.filter(pk=self.sender_notification).first()

    @staticmethod
    def get_user_name_sender(user_sender):
        user_sender_lst = str(user_sender).split(' - ')
        if len(user_sender_lst[1]) > 0:
            user_sender_name = user_sender_lst[1]
        else:
            user_sender_name = user_sender_lst[0]
        return user_sender_name

    @receiver(m2m_changed, sender=Article.likes.through)
    def notify_user_after_like_article(sender, action, instance, pk_set, **kwargs):
        """
        Сигнал для отправки уведомления автору статьи, после лайка статьи
        """
        if action == 'post_add':
            user_sender_id = [_ for _ in pk_set][0]
            user_sender = UserProfile.objects.get(user_id=user_sender_id).user
            user_sender_name = NotificationUserAfterLikeAndComment.get_user_name_sender(user_sender)
            if user_sender != instance.user:
                NotificationUserAfterLikeAndComment.objects.create(
                    recipient_notification=instance.user,
                    sender_notification=user_sender.pk,
                    message=f'{user_sender_name} поставил лайк статье: {instance.title}'
                )
        return None

    @receiver(m2m_changed, sender=UserProfile.stars.through)
    def notify_user_after_like_author(sender, action, instance, pk_set, **kwargs):
        """
        Сигнал для отправки уведомления юзеру, которому повысили ранг
        """
        if action == 'post_add':
            user_sender_id = [_ for _ in pk_set][0]
            user_sender = UserProfile.objects.get(user_id=user_sender_id).user
            user_sender_name = NotificationUserAfterLikeAndComment.get_user_name_sender(user_sender)
            if user_sender != instance.user:
                NotificationUserAfterLikeAndComment.objects.create(
                    recipient_notification=instance.user,
                    sender_notification=user_sender.pk,
                    message=f'{user_sender_name} повысил Ваш ранг!'
                )
        return None

    @receiver(m2m_changed, sender=ArticleComment.likes.through)
    def notify_user_after_like_comment(sender, action, instance, pk_set, **kwargs):
        """
        Сигнал для отправки уведомления автору комментария, после лайка комментария
        """
        if action == 'post_add':
            user_sender_id = [_ for _ in pk_set][0]
            user_sender = UserProfile.objects.get(user_id=user_sender_id).user
            user_sender_name = NotificationUserAfterLikeAndComment.get_user_name_sender(user_sender)
            if len(instance.text) > 60:
                comment = f'{instance.text[:60]}...'
            else:
                comment = instance.text
            if user_sender != instance.user:
                NotificationUserAfterLikeAndComment.objects.create(
                    recipient_notification=instance.user,
                    sender_notification=user_sender.pk,
                    message=f'{user_sender_name} поставил лайк комментарию: {comment}'
                )
        return None

    @receiver(post_save, sender=ArticleComment)
    def notify_user_after_added_comment(sender, instance, **kwargs):
        """
        Сигнал для отправки уведомления автору статьи, после добавления комментария к статье
        """
        user_sender_name = NotificationUserAfterLikeAndComment.get_user_name_sender(instance.user)
        if instance.user != instance.article_comment.user:
            NotificationUserAfterLikeAndComment.objects.create(
                recipient_notification=instance.article_comment.user,
                sender_notification=instance.user.pk,
                message=f'{user_sender_name} оставил комментарий к статье: {instance.article_comment}'
            )
        return None


class Post(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(max_length=150)
    category = TreeForeignKey('Category',
                              on_delete=models.PROTECT,
                              related_name='posts',
                              verbose_name='Категория')
    content = models.TextField(verbose_name='Содержание')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'


class Category(MPTTModel):
    title = models.CharField(max_length=50, unique=True, verbose_name='Название')
    parent = TreeForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='children',
                            db_index=True, verbose_name='Родительская категория')
    slug = models.SlugField()

    class MPTTMeta:
        order_insertion_by = ['title']

    class Meta:
        unique_together = [['parent', 'slug']]
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def get_absolute_url(self):
        return reverse('post-by-category', args=[str(self.slug)])

    def __str__(self):
        return self.title
