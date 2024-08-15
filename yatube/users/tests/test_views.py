from django.contrib.auth import get_user_model
from django.contrib.auth.forms import forms
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserPagesTest(TestCase):
    @classmethod
    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:login'): 'users/login.html',
        }
        for address, expected_template in templates_pages_names.items():
            response = self.guest_client.get(address)
            with self.subTest(address=address):
                self.assertTemplateUsed(response, expected_template)

    def test_correct_context_create_user(self):
        """Контекст передаётся в форму для создания нового пользователя"""
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'password1': forms.PasswordInput,
            'password2': forms.PasswordInput,
        }
        form = response.context.get('form')
        for field, expected_value in form_fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(
                    form.fields[field].widget, expected_value)
        self.assertIsInstance(form.fields['username'], forms.CharField)
