from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class UserURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Автор постов')
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
            description='Описание',
        )
        cls.user = User.objects.create_user(
            username='Пользователь без постов'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='текст',
        )
        cls.another_user = User.objects.create_user(
            username='another_user')

    def setUp(self):
        self.unauthorized_user = Client()
        self.authorized_client = Client()
        self.post_author = Client()
        self.auth_author = Client()
        self.authorized_user = Client()
        self.auth_author.force_login(self.author)
        self.authorized_client.force_login(self.author)
        self.authorized_user.force_login(self.another_user)
        cache.clear()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.author}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): 'posts/create_post.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_create_list_url_redirect_anonymous(self):
        """Страница /create/ после redirect временно перемещается,
        на другой адрес."""
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, 302)

    def test_posts_detail_url_redirect_anonymous(self):
        """Страница /post_edit/ перенаправляет анонимного,
        пользователя."""
        response = self.client.get('/post_detail/')
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_user_urls_status_code(self):
        """Проверка status_code для неавторизованного пользователя."""
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'bad_slug'}): HTTPStatus.NOT_FOUND,
            reverse(
                'posts:profile',
                kwargs={'username': self.author}): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): HTTPStatus.FOUND,
            reverse(
                'posts:post_create'): HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                status_code = self.unauthorized_user.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_authorized_user_urls_status_code(self):
        """Проверка status_code для авторизованного пользователя."""
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'bad_slug'}): HTTPStatus.NOT_FOUND,
            reverse(
                'posts:profile',
                kwargs={'username': self.another_user}): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): HTTPStatus.FOUND,
            reverse(
                'posts:post_create'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_user.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_author_user_urls_status_code(self):
        """Проверка status_code для авторизированого автора."""
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'bad_slug'}): HTTPStatus.NOT_FOUND,
            reverse(
                'posts:profile',
                kwargs={'username': self.author}): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}): HTTPStatus.OK,
            reverse(
                'posts:post_create'): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                status_code = self.authorized_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_urls_redirect_client(self):
        """Редирект, когда не автор пытается редактировать пост"""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.client.get(page)
            self.assertRedirects(response, value)
