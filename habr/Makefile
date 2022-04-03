start:
	docker-compose up -d  --buil
	docker-compose exec django python manage.py migrate
	docker-compose exec django python manage.py collectstatic
	docker-compose exec django python manage.py createsuperuser

add-data:
	docker-compose exec django python manage.py filling_database

up-start:
	docker-compose up -d  --buil
	docker-compose exec django python manage.py migrate

update:
	docker-compose exec django python manage.py migrate
	docker-compose up -d  --buil

stop:
	docker-compose down -v

delete:
	docker system prune -a

postgre:
	docker-compose exec db psql --username=habr_admin --dbname=geek_habr_db

