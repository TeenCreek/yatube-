import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.another_user = User.objects.create_user(username='NotAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.edited_group = Group.objects.create(
            title='Отредактированная тестовая группа',
            slug='new-test-slug',
            description='Отредактированное тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.new_post = Post.objects.create(
            text='Новый тестовый пост',
            author=cls.user,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user_notor = Client()
        self.authorized_client.force_login(self.user)
        self.user_notor.force_login(self.another_user)

    def test_create_post(self):
        """Запись добавляется с валидной формой."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Создан тестовый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=form_data['text'],
                group=self.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_create_post(self):
        """Запись не создается  неавторизованному пользователю"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("posts:post_create")}'
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post(self):
        """Запись редактируется авторизованным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый измененный пост',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                author=self.post.author,
                text=form_data['text'],
                group=form_data['group'],
                pub_date=self.post.pub_date,
            ).exists()
        )

    def test_nonedit_post(self):
        """Запись не редактируется неавторизованным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.edited_group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                author=self.post.author,
                text=self.post.text,
                group=self.post.group,
                pub_date=self.post.pub_date,
            ).exists()
        )

    def test_form_post_edit_post_by_notauthor(self):
        """Запись не редактируется не автором поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.edited_group.id,
        }
        response = self.user_notor.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                author=self.post.author,
                text=self.post.text,
                group=self.post.group,
                pub_date=self.post.pub_date,
            ).exists()
        )

    def test_create_post_without_group(self):
        """Запись создается без группы."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый пост без группы',
            'group': ''
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.new_post.author,
                text=form_data['text'],
                group=None,
            ).exists()
        )


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Комментарий добавляется с валидной формой."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Создан тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                author=self.user,
                post=self.post.id,
                text=form_data['text'],
            ).exists()
        )

    def test_guest_create_comment(self):
        """Комментарий не создается  неавторизованному пользователю"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Создан тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count)
