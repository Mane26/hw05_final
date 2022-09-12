from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()
Number_of_characters = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаём тестовую запись в БД."""
        # И сохраняем созданную запись в качестве переменной класса
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='Тест-слаг',
            description='тест-описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='p' * Number_of_characters,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        group_title = group.title
        post = PostModelTest.post
        post_title = post.text[:Number_of_characters]
        expected_str = {
            group: group_title,
            post: post_title
        }
        for model, expected_value in expected_str.items():
            with self.subTest(model=model):
                self.assertEqual(expected_value, str(model))

    def test_post_help_text(self):
        """help_text поля title совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_test = {
            'text': 'Введите текст поста',
            'group': 'Группа с постом',
        }
        for field, expected_value in field_help_test.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verbose_name = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество',
        }
        for field, expected_value in field_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )
