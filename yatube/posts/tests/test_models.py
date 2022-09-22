from django.test import TestCase

from ..models import POST_COUNT, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='Тест-слаг',
            description='тест-описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='pppppppppppppppppppppppppp' * POST_COUNT,
        )

    def test_post_str(self):
        """Проверка __str__ у post."""
        self.assertEqual(self.post.text[:POST_COUNT], str(self.post))

    def test_post_verbose_name(self):
        """Проверка verbose_name у post."""
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество', }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = self.post._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_post_help_text(self):
        """Проверка help_text у post."""
        feild_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа с постом', }
        for value, expected in feild_help_texts.items():
            with self.subTest(value=value):
                help_text = self.post._meta.get_field(value).help_text
                self.assertEqual(help_text, expected)
