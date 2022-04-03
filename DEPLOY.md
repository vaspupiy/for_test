# 1. Организовать сервер 



1. Купить VPS
2. Купить домен
3. Добавить к домену А-запись с IP сервер


# 2. Создать юзера

Создать юзера (без root прав) и задать пароль

```
useradd -s /bin/bash -d /home/user -m user_name
passwd <name>
```


# 3. Подключить Git

[https://rtfm.co.ua/github-avtorizaciya-po-ssh-klyucham/](https://rtfm.co.ua/github-avtorizaciya-po-ssh-klyucham/) 


# 4. Подключить MakeFile


```
apt-get -y install make
```



# 5. Установить и настроить NGINX


```
sudo apt install nginx
systemctl status nginx
```


Создать файл {{site_name}}.conf в папке /etc/nginx/sites-available

Вставить в него 


```
server {
    server_name {{domain}};

    listen 80;

    location / {
        proxy_pass http://localhost:9090/;
    }
}
```



# 6. Установить и настроить LETS SCRIPT


```
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d {{domain}}
sudo systemctl status certbot.timer
```


после установки сертификата файл {{site_name}}.conf в папке /etc/nginx/sites-available измениться

после этого, надо его привести в вид


```
server {
   server_name {{domain}};
   listen 80;
   return 301 https://$host$request_uri;
}
    

server {
   server_name ssl_{{domain}};
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/geek-habr.ru/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/geek-habr.ru/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
   
   location / {
      proxy_pass http://0.0.0.0:9090;
      include proxy_params;
      
    }
   
      location /static/ {
        root /home/diplom/habr/;
    }
    
        location /media/ {
        root /home/diplom/habr/;
    }

}
```


В итоге скопировать полученный файл {{site_name}}.conf из папки /etc/nginx/sites-available в папку /etc/nginx/sites-enabled


# 7. Установить Docker и дать созданному пользователю права

Установка

[https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-ru](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-ru)

Дать юзеру права


```
sudo usermod -aG docker $USER
sudo reboot
```



# 8. Подготовить и запустить проект



1. Зайти на сервер под созданным пользователем (не  root) 
2. Создать папку для проекта
3. Перейти в папку и сделать git clone
4. Вставить нужные домены в файл diploma-project/habr/settings.yaml в переменную CSRF_TRUSTED_ORIGINS
5. Изменить настройки статики в файле habr/habr/settings.py
5. Запустить проект с помощью MakeFile


# 9. Команды Makefiles

Команды запускать из папки где лежит Makefiles


```
#первый запуск проекта
make start

#заполнить БД тестовыми данными
make add-data

#если на сайте не отображаются все данные из БД
make up-start

#применить изменения в файлах сайта
make update

#остановить проект
make stop

#удалить все созданные docker контейнеры (применить если нужно удалить проект с диска и удалить все дочерние docker контейнеры)
make delete

#войти в postgre
make postgre
```

