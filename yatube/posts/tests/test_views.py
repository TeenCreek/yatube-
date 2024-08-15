import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context.get('page_obj')[0]
        post_contexts = {
            post.text: self.post.text,
            post.author: self.post.author,
            post.group: self.post.group,
            post.id: self.post.id,
            post.image: self.post.image
        }
        for field, expected_value in post_contexts.items():
            with self.subTest(context=field):
                self.assertEqual(field, expected_value)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        obj = response.context['page_obj'].object_list[0]
        group_obj = response.context['group']
        self.assertEqual(obj.author, self.post.author)
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(obj.group, self.post.group)
        self.assertEqual(obj.image, self.post.image)
        self.assertEqual(group_obj, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'TestUser'}))
        post_obj = response.context['page_obj'].object_list[0]
        author_obj = response.context['author']
        self.assertEqual(post_obj.author, self.post.author)
        self.assertEqual(post_obj.text, self.post.text)
        self.assertEqual(post_obj.group, self.post.group)
        self.assertEqual(post_obj.image, self.post.image)
        self.assertEqual(author_obj, self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context.get('post')
        post_context = {
            post.text: self.post.text,
            post.author: self.post.author,
            post.group: self.post.group,
            post.id: self.post.id,
            post.image: self.post.image
        }
        for field, expected_value in post_context.items():
            with self.subTest(context=field):
                self.assertEqual(field, expected_value)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected_value in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected_value)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected_value in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected_value)
        self.assertFalse(response.context.get('is_edit'))

    def test_check_group_not_in_mistake_group_list_page(self):
        """Пост не попадает в другую группу."""
        another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-test-slug',
            description='Другое тестовое описание',
        )
        another_post = Post.objects.create(
            text='Другой тестовый пост',
            author=self.user,
            group=another_group,
        )
        post_count = Post.objects.filter(group=another_group).count()
        response = self.guest_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )
        )
        self.assertEqual(
            Post.objects.filter(group=another_group).count(),
            post_count
        )
        self.assertNotIn(another_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    POST_COUNT = 13
    POST_COUNT_ON_1_PAGE = 10
    POST_COUNT_ON_2_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        Post.objects.bulk_create(
            [Post(
                text=f'Тестовый пост: {post}',
                author=cls.user,
                group=cls.group,
            )
                for post in range(cls.POST_COUNT)
            ]
        )

    def setUp(self):
        self.unauthorized_client = Client()

    def test_paginator_on_pages(self):
        """Пагинации на страницах."""
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for reverses in url_pages:
            with self.subTest(reverses=reverses):
                self.assertEqual(len(self.unauthorized_client.get(
                    reverses).context.get('page_obj')),
                    self.POST_COUNT_ON_1_PAGE
                )
                self.assertEqual(len(self.unauthorized_client.get(
                    reverses + '?page=2').context.get('page_obj')),
                    self.POST_COUNT_ON_2_PAGE)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='TestAuthorClient')
        cls.follower = User.objects.create(username='TestFollowerClient')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self):
        self.guest_user = Client()
        self.follower_client = Client()
        self.author_client = Client()
        self.follower_client.force_login(self.follower)
        self.author_client.force_login(self.author)

    def test_follow(self):
        """Пользователь пожет подписаться на автора."""
        follow_count = Follow.objects.count()
        self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.author,
                author=self.follower
            )
        )

    def test_unfollow(self):
        """Пользователь может отписаться от автора."""
        Follow.objects.create(
            user=self.author,
            author=self.follower
        )
        follow_count = Follow.objects.count()
        self.author_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.follower}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.author,
                author=self.follower
            )
        )

    def test_posts_only_followers(self):
        """Запись появляется только у тех пользователей,
        которые подписаны на автора."""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(
            self.post,
            response.context['page_obj'].object_list
        )

    def test_posts_not_only_followers(self):
        """Запись не появляется у пользователей,
        которые не подписаны на автора."""
        response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            self.post,
            response.context['page_obj'].object_list
        )

    def test_notauthorized_client_follow(self):
        """Неавторизованный пользователь не может подписаться на автора"""
        follow_count = Follow.objects.count()
        self.guest_user.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_author_on_author(self):
        """Пользователь не может подписаться сам на себя"""
        Follow.objects.create(
            user=self.author,
            author=self.follower
        )
        follow_count = Follow.objects.count()
        self.author_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower}
            )
        )
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertNotEqual(follow.user.id, self.follower.id)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache(self):
        """Страница сохраняется в кеше"""
        first_response = self.authorized_client.get(reverse('posts:index'))
        first_post = first_response.content

        self.post.delete()

        second_response = self.authorized_client.get(reverse('posts:index'))
        second_posts = second_response.content

        self.assertEqual(second_posts, first_post)
        cache.clear()

        third_response = self.authorized_client.get(reverse('posts:index'))
        third_posts = third_response.content

        self.assertNotEqual(third_posts, first_post)
