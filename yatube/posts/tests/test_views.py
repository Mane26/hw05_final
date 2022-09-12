from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()

POST_NUM_ONE_PAGE = 10
POST_SUM_FOR_PAGINATOR = 12


class TestTemplatePages(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создадим запись в БД."""
        cls.author = User.objects.create_user(
            username='Автор постов'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='address',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='текст',
        )
        cls.user = User.objects.create_user(
            username='Пользователь без постов'
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.guest_client = Client()
        self.auth_author = Client()
        self.auth_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_pages_templates(self):
        """URL-адреса используют шаблон posts/index.html."""
        reverse_index = reverse('posts:index')
        reverse_group = reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        reverse_user = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        reverse_post = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        template_pages_names = {
            reverse_index: 'posts/index.html',
            reverse_group: 'posts/group_list.html',
            reverse_user: 'posts/profile.html',
            reverse_post: 'posts/post_detail.html',
        }
        for reverse_name, templates in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, templates)

    def test_template_for_urls_author(self):
        """URL-адреса используют шаблон posts/create_post.html."""
        reverse_posts_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        urls_set = {
            reverse_posts_edit: 'posts/create_post.html'
        }
        for reverse_name, template in urls_set.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_template_for_urls_authorized_user(self):
        """URL-адреса используют шаблон posts/create_post.html."""
        reverse_posts_create = reverse('posts:post_create')
        urls_set = {
            reverse_posts_create: 'posts/create_post.html'
        }
        for reverse_name, template in urls_set.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class TestContextPages(TestCase):
    @classmethod
    def setUpClass(cls):
        # Создадим запись в БД
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='Автор постов'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='address',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='текст',
            group=cls.group,
        )
        cls.user = User.objects.create_user(
            username='Пользователь без постов'
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.guest_client = Client()
        self.auth_author = Client()
        self.auth_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.user_2 = User.objects.create_user(
            username='Второй юзер'
        )
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        cache.clear()

    def test_index_context(self):
        # Проверка словаря контекста главной страницы (в нём передаётся форма)
        """Шаблон index сформирован с правильным контекстом."""
        reverse_address = reverse('posts:index')
        response = self.authorized_client.get(reverse_address)
        context_page = response.context.get('page_obj')
        for post in context_page:
            self.assertIsInstance(post, Post)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)

    def test_group_posts_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        reverse_address = reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        )
        response = self.authorized_client.get(reverse_address)
        context_page = response.context.get('page_obj')
        for post in context_page:
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)

    def test_profile_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        reverse_address = reverse(
            'posts:profile',
            kwargs={'username': self.author.username}
        )
        response = self.authorized_client.get(reverse_address)
        context_page = response.context.get('page_obj')
        for post in context_page:
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text_0 = {response.context['post'].text: 'текст',
                       response.context['post'].group: self.group,
                       response.context['post'].author: self.user.username}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_post_edit_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        reverse_address = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        response = self.authorized_client.get(reverse_address)
        post_id = Post.objects.get(pk=self.post.pk).text
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(
                    field_name=field_name,
                    field_type=field_type
            ):
                form_field = response.context.get('form').fields.get(
                    field_name)
                self.assertEqual(post_id, self.post.text)
                self.assertIsInstance(form_field, field_type)

    def test_create_post_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        reverse_address = reverse(
            'posts:post_create'
        )
        response = self.authorized_client.get(reverse_address)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(
                    field_name=field_name,
                    field_type=field_type
            ):
                form_field = response.context.get(
                    'form'
                ).fields.get(field_name)
                self.assertIsInstance(form_field, field_type)

    def test_create_post_correct(self):
        reverse_index = reverse('posts:index')
        reverse_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug}
        )
        reverse_profile = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        response_index = self.authorized_client.get(reverse_index)
        response_group_list = self.authorized_client.get(reverse_group_list)
        response_profile = self.authorized_client.get(reverse_profile)
        context_index = response_index.context.get('page_obj')
        context_group_list = response_group_list.context.get('page_obj')
        context_profile = response_profile.context.get('page_obj')
        self.assertNotIn(self.post.id, context_index)
        self.assertNotIn(self.post.id, context_group_list)
        self.assertNotIn(self.post.id, context_profile)


class TestPaginatorPages(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='Автор постов'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='address',
            description='Описание',
        )
        cls.post_list = []
        for i in range(POST_SUM_FOR_PAGINATOR):
            cls.post_list.append(Post(
                author=cls.author,
                text='текст',
                group=cls.group,
            ))
        cls.post = Post.objects.bulk_create(cls.post_list)

    def setUp(self):
        self.auth_author = Client()
        self.auth_author.force_login(self.author)
        cache.clear()

    def test_paginator_for_pages(self):
        # Здесь создаются фикстуры: клиент и 13 тестовых записей.
        pages = {
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            ),
        }
        for page in pages:
            with self.subTest(page=page):
                # Проверка: количество постов на первой и второй странице
                response_page_number_one = self.auth_author.get(page)
                response_page_number_two = self.auth_author.get(
                    page + '?page=2'
                )
                context_for_first = response_page_number_one.context.get(
                    'page_obj'
                )
                context_for_second = len(
                    response_page_number_two.context.get('page_obj')
                )
                post_for_second = len(self.post) - POST_NUM_ONE_PAGE
                self.assertIsInstance(context_for_first, Page)
                self.assertEqual(len(context_for_first), POST_NUM_ONE_PAGE)
                self.assertEqual(context_for_second, post_for_second)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(
            username='post_autor',
        )
        cls.post_follower = User.objects.create(
            username='post_follower',
        )
        cls.post = Post.objects.create(
            text='Подпишись на меня',
            author=cls.post_autor,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)
        cache.clear()

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.post_follower.id)
        self.assertEqual(follow.user_id, self.post_autor.id)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.post_autor,
            author=self.post_follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)
