### hw05_final - Проект спринта: подписки на авторов, спринт 6 в Яндекс.Практикум

# Спринт 6 - Проект спринта: подписки на авторов
# hw05_final - Проект спринта: подписки на авторов, Яндекс.Практикум.

Покрытие тестами проекта Yatube из спринта 6 Питон-разработчика бекенда Яндекс.Практикум. Все что нужно, это покрыть тестами проект, в учебных целях. Реализована система подписок/отписок на авторов постов.

### ЗАМЕЧАНИЕ:
- Не работает статика должным образом, пофиксить, переходом на Django 3 или 4

Стек:

- Python 3.10.5
- Django==2.2.28
- mixer==7.1.2
- Pillow==9.0.1
- pytest==6.2.4
- pytest-django==4.4.0
- pytest-pythonpath==0.7.3
- requests==2.26.0
- six==1.16.0
- sorl-thumbnail==12.7.0
- Pillow==9.0.1
- django-environ==0.8.1

## Настройка и запуск на ПК
Клонируем проект:

- git clone https://github.com/Mane26/hw05_final.git

Переходим в папку с проектом:
- cd hw05_final

Устанавливаем виртуальное окружение:
- python -m venv venv

Активируем виртуальное окружение:
- source venv/Scripts/activate

Для деактивации виртуального окружения выполним (после работы):
- deactivate

Устанавливаем зависимости:
- python -m pip install --upgrade pip
- pip install -r requirements.txt

Применяем миграции:
- python yatube/manage.py makemigrations
- python yatube/manage.py migrate

Создаем супер пользователя:
- python yatube/manage.py createsuperuser
При желании делаем коллекцию статики (часть статики уже загружена в репозиторий в виде исключения):

python yatube/manage.py collectstatic
Предварительно сняв комментарий с:

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
И закомментировав:

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
Иначе получим ошибку: You're using the staticfiles app without having set the STATIC_ROOT setting to a filesystem path.

В папку с проектом, где файл settings.py добавляем файл .env куда прописываем наши параметры:

- SECRET_KEY='Ваш секретный ключ'
- ALLOWED_HOSTS='127.0.0.1, localhost'
- DEBUG=True

Не забываем добавить в .gitingore файлы:
- .env
- .venv
