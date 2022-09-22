import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post, User

POST_SUM_FOR_PAGINATOR = 13
page_number_one = 10
page_number_two = 3

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Название',
            slug='address',
            description='Описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.user = User.objects.create_user(
            username='Пользователь без постов'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def check_post_info(self, post):
        """Проверка атрибутов поста"""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)
            self.assertEqual(post.post, self.post.post.id)


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
            text='текст',
            author=cls.author,
            group=cls.group,
        )
        cls.user = User.objects.create_user(
            username='Пользователь без постов'
        )
        cls.client = Client()

    def setUp(self):
        self.auth_author = Client()
        self.client_auth = Client()
        self.auth_author.force_login(self.author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.user_2 = User.objects.create_user(
            username='Второй юзер'
        )
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        cache.clear()

    def check_post_info(self, post):
        """Проверка атрибутов post"""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.image, self.post.image)

    def test_views_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            f'{self.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{self.user.username}'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html'}

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                error_name = f'Ошибка: {adress} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_post_info(response.context['page_obj'][0])

    def test_groups_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_info(response.context['page_obj'][0])

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))
        self.check_post_info(response.context['post'])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = TestContextPages.client.get(
            reverse('posts:profile', args=[TestContextPages.author.username])
        )
        post = TestContextPages.post
        author = TestContextPages.author
        response_post = response.context.get('page_obj').object_list[0]
        post_author = response_post.author
        post_group = response_post.group
        post_text = response_post.text
        post_image = response_post.image
        self.assertEqual(post_author, author)
        self.assertEqual(post_group, TestContextPages.group)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)

    def check_post_in_page(self, url, text, user, group):
        response = self.client_auth.get(url)
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(paginator.count, 1)
            post = response.context['page'][0]
        else:
            post = response.context['post']
        self.assertEqual(post.text, text)
        self.assertEqual(post.author, user)
        self.assertEqual(post.group, group)

    def test_post_appears_on_pages(self):
        """ После публикации поста новый пост
        попадает на первую позицию в контексте."""
        new_post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.group)
        response = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(
            response.context['page_obj'].object_list[0], new_post,
            'Новый пост не выводится первым')

    def test_post_added_correctly_user2(self):
        """После публикации, пост не попадает в чужую группу."""
        group2 = Group.objects.create(title='Тестовая группа 2',
                                      slug='test_group2')
        posts_count = Post.objects.filter(group=self.group).count()
        post = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user_2,
            group=group2)
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}))
        group = Post.objects.filter(group=self.group).count()
        profile = response_profile.context['page_obj']
        self.assertEqual(group, posts_count, 'поста нет в другой группе')
        self.assertNotIn(post, profile,
                         'поста нет в группе другого пользователя')


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
        cls.templates = {
            1: reverse('posts:index'),
            2: reverse('posts:group_list', args=[cls.group.slug]),
            3: reverse('posts:profile', args=[cls.author.username])
        }

    def setUp(self):
        self.auth_author = Client()
        self.auth_author.force_login(self.author)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на первую страницую."""
        templates = {
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
        for page in templates:
            with self.subTest(page=page):
                response_page_number_one = self.auth_author.get(page)
                context_for_first = response_page_number_one.context.get(
                    'page_obj'
                )
                self.assertIsInstance(context_for_first, Page)
                self.assertEqual(len(context_for_first), page_number_one)

    def test_second_page_contains_three_records(self):
        """Paginator предоставляет ожидаемое количество постов
         на вторую страницую."""
        templates = {
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
        for page in templates:
            with self.subTest(page=page):
                response_page_number_two = self.auth_author.get(
                    page + '?page=2'
                )
                context_for_second = len(
                    response_page_number_two.context.get('page_obj')
                )
                post_for_second = len(self.post) - page_number_one
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
        self.client_auth = Client()
        self.user1 = User.objects.create_user(username="mane")
        self.user2 = User.objects.create_user(username="narina")
        self.client_auth.force_login(self.user1)
        self.user = User.objects.create_user(username='user', password='pass')
        self.user.save()
        self.author_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)
        self.text = "Поэты 19века"
        cache.clear()

    def response_get(self, name, rev_args=None, followed=True):
        return self.client.get(
            reverse(
                name,
                kwargs=rev_args
            ),
            follow=followed
        )

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        Follow.objects.create(user=self.user1, author=self.user2)
        is_follow = Follow.objects.filter(user=self.user1,
                                          author=self.user2).count()
        self.assertEqual(is_follow, 1)
        response_unsubscribe = self.client_auth.post(
            reverse('posts:profile_unfollow',
                    args=(self.user2,)), follow=True)
        self.assertIn("Подписаться", response_unsubscribe.content.decode())

        follow_obj = Follow.objects.filter(user=self.user1,
                                           author=self.user2).count()
        self.assertEqual(follow_obj, 0)

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

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_autor)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка записей у тех кто не подписан."""
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
