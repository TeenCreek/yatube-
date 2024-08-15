
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from users.forms import CreationForm

User = get_user_model()


class UserFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_new_user_create_valid_form(self):
        """Форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'username': 'TestNewUser',
            'password1': 'edcwsxqaz4o@',
            'password2': 'edcwsxqaz4o@',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                username='TestNewUser',
            ).exists()
        )
