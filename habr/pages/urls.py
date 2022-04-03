from django.urls import path

from pages.views import detail

app_name = 'pages'

urlpatterns = [
    path('<str:slug>/', detail, name='detail'),
]
