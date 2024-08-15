from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.not_author_user = User.objects.create_user(username='TestUser2')
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
        cls.post2 = Post.objects.create(
            text='Тестовый пост',
            author=cls.not_author_user,
            group=cls.group,
        )
        cls.nonauthorized_urls = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.authorized_urls = {
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        cls.redirect_urls = {
            f'/posts/{cls.post.id}/edit/':
                f'/auth/login/?next=/posts/{cls.post.id}/edit/',
            '/create/': '/auth/login/?next=/create/',
            '/follow/': '/auth/login/?next=/follow/',
            f'/profile/{cls.user.username}/follow/':
                f'/auth/login/?next=/profile/{cls.user.username}/follow/',
            f'/profile/{cls.user.username}/unfollow/':
                f'/auth/login/?next=/profile/{cls.user.username}/unfollow/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_not_author_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_not_author_client.force_login(self.not_author_user)

    def test_urls_for_all_users(self):
        """Проверка доступа на страницы для всех пользователей."""
        for address in self.nonauthorized_urls.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_authorized_users(self):
        """Проверка доступа на страницы для авторизованного пользователя."""
        for address in self.authorized_urls.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_for_unauthorized_users(self):
        """Редирект неавторизованного пользователя"""
        for address, template in self.redirect_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, template)

    def test_urls_redirect_for_not_author_user(self):
        """Авторизованный пользователь не имеет доступа к редактированию
        чужих постов"""
        response = self.authorized_not_author_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True,
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_uses_correct_template_for_authorized_clients(self):
        """URL-адрес использует соответствующий шаблон
        для авторизованного пользователя."""
        for address, template in self.authorized_urls.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_nonauthorized_clients(self):
        """URL-адрес использует соответствующий шаблон
        для неавторизованного пользователя."""
        for address, template in self.nonauthorized_urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_404_template(self):
        """Несуществующий URL-адрес использует соответствующий шаблон."""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEquals(response.status_code, HTTPStatus.NOT_FOUND)
