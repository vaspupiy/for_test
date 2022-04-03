import random
import os
import requests
import datetime

from django.utils import timezone
from mimesis import Text, Person, Datetime
from mimesis import Internet

from django.core.management.base import BaseCommand
from django.core.files import File

from mainapp.models import Article, ArticleComment, ArticleCategories
from authapp.models import User, UserProfile


class Command(BaseCommand):
    help = 'Create Categories article, Articles, Likes and Comments'

    def handle(self, *args, **options):
        # GENERATE PROJECTS
        text = Text('ru')

        # CREATE USERS
        person = Person()
        birthday = Datetime()

        print('Заполняю таблицу USERS')

        for _ in range(10):
            username_ = person.username(mask='C')
            password_ = person.password(length=8)

            print(f'Логин: {username_} / Пароль: {password_}')

            user = User(
                username=username_,
                email=person.email())

            user.set_password(password_)
            user.save()

        print('Заполняю таблицу USERS PROFILE')
        for item in UserProfile.objects.all():
            name = person.name()

            item.name = name
            item.birthday = birthday.formatted_datetime(fmt="%Y-%m-%d")
            item.bio = "Этот автор - самый крутой. Статьи у него пушка-бомба!"
            item.stars.set(User.objects.all())
            item.rating = random.randrange(50, 400)
            item.previous_article_rating = random.randrange(1, 50)

            img_url = Internet().stock_image(width=50, height=50, keywords=['лицо'])
            img_file = requests.get(img_url)

            file_name = f'{name}.png'
            with open(file_name, 'wb') as file:
                file.write(img_file.content)

            with open(file_name, 'rb') as file:
                data = File(file)
                item.avatar.save(file_name, data, True)

            os.remove(file_name)
            # заполняется поле stars у таблицы USERS PROFILE
            for _ in range(random.randint(0, 10)):
                user_liked = random.choice(User.objects.all())
                if user_liked in item.stars.all():
                    item.stars.remove(user_liked)
                else:
                    item.stars.add(user_liked)

            item.save()

        # CREATE ARTICLE CATEGORIES
        ARTICLE_CATEGORIES = ['Дизайн', 'Веб-разработка', 'Мобильная разработка', 'Маркетинг']

        print('Заполняю таблицу ARTICLE CATEGORIES')
        for categories in ARTICLE_CATEGORIES:
            new_categories = ArticleCategories(name=categories)
            new_categories.save()

        # CREATE ARTICLES
        print('Заполняю таблицу ARTICLES')
        for i in range(20):
            # create article
            new_article = Article()
            # set categories
            new_article.categories = random.choice(ArticleCategories.objects.all())
            # set author
            new_article.user = random.choice(User.objects.all())
            new_article.title = f'Заголовок статьи #{i} автора {new_article.user.username}'
            new_article.subtitle = f'Падзаголовок статьи #{i} автора {new_article.user.username}'
            new_article.text = text.text(quantity=15)
            new_article.status = 'A'

            # create and set article images
            img_url = Internet().stock_image(width=390, height=300, keywords=['природа'])
            img_file = requests.get(img_url)

            file_name = f'{text.word()}.png'
            with open(file_name, 'wb') as file:
                file.write(img_file.content)

            with open(file_name, 'rb') as file:
                data = File(file)
                new_article.main_img.save(file_name, data, True)

            os.remove(file_name)
            # заполняется поле likes у таблицы ARTICLES
            for _ in range(random.randint(0, 10)):
                user_liked = random.choice(User.objects.all())
                if user_liked in new_article.likes.all():
                    new_article.likes.remove(user_liked)
                else:
                    new_article.likes.add(user_liked)

            # save article
            new_article.save()
            new_article.tags.add(*[text.word() for _ in range(4)])

            new_article.created_timestamp = \
                timezone.localtime(timezone.now()) - datetime.timedelta(days=random.choice([_ for _ in range(0, 10)]))
            new_article.save()

        # CREATE COMMENTS
        print('Заполняю таблицу COMMENTS')
        for item in User.objects.all():
            count = random.choice([i for i in range(0, 10)])
            for i in range(0, count):
                new_comment = ArticleComment(text=text.text(quantity=2))
                new_comment.article_comment = random.choice(Article.objects.all())
                new_comment.user = item
                new_comment.save()
                # заполняется поле likes у таблицы COMMENTS
                for _ in range(random.randint(0, 10)):
                    user_liked = random.choice(User.objects.all())
                    if user_liked in new_comment.likes.all():
                        new_comment.likes.remove(user_liked)
                    else:
                        new_comment.likes.add(user_liked)
