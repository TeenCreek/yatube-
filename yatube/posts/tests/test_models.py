from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Group, Post

User = get_user_model()

POST_MAX_LENGTH = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Текст для поста',
            author=cls.user,
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""
        self.assertEqual(self.post.__str__(), self.post.text[:POST_MAX_LENGTH])

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа поста',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым"""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""
        self.assertEqual(self.group.__str__(), self.group.title)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым"""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'URL-адрес',
            'description': 'Описание',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Текст для поста',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='Текст комментария',
            author=cls.user,
            post=cls.post,
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым"""
        comment = CommentModelTest.comment
        field_verboses = {
            'text': 'Текст комментария',
            'author': 'Автор комментария',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым"""
        comment = CommentModelTest.comment
        field_help_texts = {
            'text': 'Введите текст комментария',
            'post': 'Пост, к которому относится комментарий'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).help_text, expected_value
                )
