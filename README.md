Workflow status
![workflow](https://github.com/Darya-Kuzmich/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## FOODGRAM
Сайт, где пользователи могут делиться своими рецептами и подписываться на других пользователей, добавлять понравившиеся рецепты в избранное и список покупок, который можно будет скачать в формате PDF.

### Технологии
- Python 3.8
- Django 3.1
- Django REST Framework 3.12
- PostgreSQL 12.4  
- Nginx 1.19.3
- Gunicorn 20.0.4
- Docker 3.8

### Запуск проекта:
Для работы с проектом необходимо установить Docker https://docs.docker.com/engine/install/

Клонировать репозиторий:
- git clone https://github.com/Darya-Kuzmich/foodgram-project-react.git

В директории foodgram-project-react/backend/foodgram создать файл .env и пометсить туда переменные в формате имя_переменной=значение. Пример файла:
- SECRET_KEY=django_secret_key
- DJANGO_ALLOWED_HOSTS=django_allowed_hosts
- DB_ENGINE=django.db.backends.postgresql
- POSTGRES_DB=postgres_db
- POSTGRES_USER=postgres_user
- POSTGRES_PASSWORD=postgres_password
- DB_HOST=db
- DB_PORT=5432

Далее в директории foodgram-project-react/infra выполнить команду:
- docker-compose up -d --build
- Создание миграций и collectstatic будут выполнены автоматрически.
- Создание суперпользователя: sudo docker exec infra_backend_1 python manage.py createsuperuser
- Загрузка фикстур: sudo docker exec infra_backend_1 python manage.py load_data
- Для корректной работы сайта нужно через админку создать пару тегов.

### Разработчик:
Проект выполнила Кузьмич Дарья в рамках учебной программы по backend-разработке Яндекс.Практикум.
