from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост. Тестовый пост'
        )
        cls.public_url = (
            ('/', 'posts/index.html'),
            ('/group/test-slug/', 'posts/group_list.html'),
            ('/profile/HasNoName/', 'posts/profile.html'),
            ('/posts/1/', 'posts/post_detail.html'),
        )

        cls.private_url = (
            ('/create/', 'posts/create_post.html'),
            ('/posts/1/edit/', 'posts/create_post.html'),
            ('/follow/', 'posts/follow.html')
        )

    def setUp(self):
        self.user = User.objects.get(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in (PostURLTests.public_url
                                  + PostURLTests.private_url):
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_redirect_anonymous(self):
        """Страницы перенаправляют анонимного пользователя."""
        self.guest_client = Client()
        login_url = reverse('users:login')
        create_url = reverse('posts:post_create')
        url_names = (
            ('/create/', f'{login_url}?next={create_url}'),
        )
        for address, redirect in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        self.guest_client = Client()
        for address, template in PostURLTests.public_url:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_authorized(self):
        """Страницы доступны авторизованному пользователю."""
        for address, template in PostURLTests.private_url:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexist_url(self):
        """Страница /unexisting_page/ не существует"""
        self.guest_client = Client()
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
