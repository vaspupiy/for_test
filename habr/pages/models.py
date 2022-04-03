from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.utils import timezone


class BusinessDirections(models.Model):
    """Таблица Напровлений бизнеса(департаменты)"""

    id = models.BigAutoField(primary_key=True, editable=False, verbose_name='id')
    direction = models.CharField(max_length=100, verbose_name='Наименование направления')

    class Meta:
        db_table = 'wdcnext_business_directions'
        verbose_name = 'Таблица Напровлений бизнеса(департаменты)'


class AccessCategories(models.Model):
    """Категории доступа"""

    id = models.BigAutoField(primary_key=True, editable=False, verbose_name='id')
    Category = models.CharField(max_length=100, verbose_name='Наименование категории')

    class Meta:
        db_table = 'wdcnext_access_categories'
        verbose_name = 'Категории доступа'


class Specializations(models.Model):
    """Таблица Специализации"""

    id = models.BigAutoField(primary_key=True, editable=False, verbose_name='id')
    specialization = models.CharField(max_length=100, verbose_name='Наименование специализации')

    class Meta:
        db_table = 'wdcnext_specializations'
        verbose_name = 'Таблица Специализации'


class TypeOfPage(models.Model):
    """Тип страницы(лендинга)"""

    id = models.BigAutoField(primary_key=True, editable=False, verbose_name='id')
    type_of_page = models.CharField(max_length=100, verbose_name='Тип страницы')

    class Meta:
        db_table = 'wdcnext_type_of_page'
        verbose_name = 'Таблица Типы страницы(лендинга)'


class Pages(models.Model):
    """Модель страницы лендинга"""

    id = models.BigAutoField(primary_key=True, editable=False, verbose_name='id')
    page_type = models.ForeignKey(TypeOfPage, on_delete=models.DO_NOTHING, verbose_name='Тип лэндинга')
    business_direction = models.ForeignKey(BusinessDirections, on_delete=models.DO_NOTHING, related_name='page',
                                           verbose_name='Направление бизнеса')
    header = models.CharField(max_length=120, verbose_name="Заголовок")
    slug = models.SlugField(max_length=250, unique=True, db_index=True, verbose_name="Символьный код страницы")
    active = models.BooleanField(default=False, verbose_name='Активен', db_index=True)
    date_start = models.DateTimeField(default=timezone.now, verbose_name='Начало эксплуатации')
    # date_start = models.DateTimeField(default=timezone.localtime(timezone.now()),
    #                                   verbose_name='Начало эксплуатации')
    date_end = models.DateTimeField(null=True, blank=True, default=None, verbose_name='Окончание эксплуатации')
    content = RichTextUploadingField(config_name='awesome_ckeditor', verbose_name='Код страницы HTML', blank=True)
    tags = models.JSONField(blank=True, null=True, verbose_name='Теги')
    # access_category = models.ForeignKey(AccessCategories, on_delete=models.DO_NOTHING, related_name='page',
    #                                     verbose_name='Категории доступа')
    specialization = models.ForeignKey(Specializations, on_delete=models.DO_NOTHING, related_name='page',
                                       verbose_name='Специальность')
    seo_title = models.CharField(verbose_name='SEO title', max_length=120, null=True, blank=True)
    seo_description = models.CharField(verbose_name='SEO description', max_length=255, null=True, blank=True)
    sending_addresses = models.JSONField(verbose_name='Адреса отправки заявки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='изменен')

    class Meta:
        db_table = 'wdcnext_pages'
        verbose_name = 'Таблица страниц сайта (лендинги)'
