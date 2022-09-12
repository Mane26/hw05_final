from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создадим запись в БД для проверки доступности
        адреса user/test-slug/."""
        cls.author = User.objects.create_user(username='Автор постов')
        cls.group = Group.objects.create(
            title='Название',
            slug='address',
            description='Описание',
        )
        cls.user = User.objects.create_user(
            username='Пользователь без постов'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='текст',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.auth_author = Client()
        self.auth_author.force_login(self.author)
        # Авторизуем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_urls_for_everyone(self):
        """Страницы  доступны любому пользователю."""
        reverse_group = reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        )
        reverse_user = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        reverse_post = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        urls_list = [
            '/',
            reverse_group,
            reverse_user,
            reverse_post,
        ]
        for urls in urls_list:
            response = self.guest_client.get(urls)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_urls(self):
        """Проверяем не существующую страницу."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_template_urls_for_everyone(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        reverse_group = reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        )
        reverse_user = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        reverse_post = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        urls_set = {
            '/': 'posts/index.html',
            reverse_group: 'posts/group_list.html',
            reverse_user: 'posts/profile.html',
            reverse_post: 'posts/post_detail.html',
        }
        for urls, template in urls_set.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(urls)
                self.assertTemplateUsed(response, template)

    def test_urls_for_author(self):
        """URL-адрес использует соответствующий шаблон."""
        reverse_post_for_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        urls_list = [
            reverse_post_for_edit,
        ]
        for urls in urls_list:
            response = self.auth_author.get(urls)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_for_urls_author(self):
        """URL-адрес использует соответствующий шаблон."""
        reverse_post_for_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        urls_set = {
            reverse_post_for_edit: 'posts/create_post.html'
        }
        for urls, template in urls_set.items():
            with self.subTest(urls=urls):
                response = self.auth_author.get(urls)
                self.assertTemplateUsed(response, template)

    def test_urls_for_authorized_user(self):
        """Доступ авторизованного пользователя."""
        urls_list = [
            '/create/',
        ]
        response = self.authorized_client.get('/create/')
        for urls in urls_list:
            response = self.authorized_client.get(urls)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_for_urls_authorized_user(self):
        """URL-адрес использует соответствующий шаблон,
        для авторизованного пользователя."""
        urls_set = {
            '/create/': 'posts/create_post.html'
        }
        response = self.authorized_client.get('/create/')
        for urls, template in urls_set.items():
            with self.subTest(urls=urls):
                response = self.authorized_client.get(urls)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_create_list_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_posts_detail_url_redirect_anonymous(self):
        """Страница /post_edit/ перенаправляет анонимного
        пользователя.
        """
        response = self.client.get('/post_detail/')
        self.assertEqual(response.status_code, 404)
