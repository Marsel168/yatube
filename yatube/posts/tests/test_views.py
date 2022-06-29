import tempfile
import shutil

from django.test import TestCase, Client, override_settings
from ..forms import PostForm
from ..models import Post, Group, Comment, Follow
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
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
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий'
        )
        cls.templates_pages_names = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'}
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ), 'posts/post_detail.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ), 'posts/create_post.html'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_with_correct_context(self):
        """Картинка передается в списке контекста"""
        for num_page in range(4):
            url, _ = PostViewTests.templates_pages_names[num_page]
            first_object = self.authorized_client.get(url).context.get('post')
            self.assertEqual(first_object.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in PostViewTests.templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        url, _ = PostViewTests.templates_pages_names[0]
        response = self.authorized_client.get(url)
        first_object = response.context.get('post')
        context = (
            (first_object.text, PostViewTests.post.text),
            (first_object.author, PostViewTests.post.author),
            (first_object.group, PostViewTests.post.group),
            (first_object.pub_date, PostViewTests.post.pub_date)
        )
        self.check_context(context)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        url, _ = PostViewTests.templates_pages_names[1]
        response = self.authorized_client.get(url)
        group = response.context.get('group')
        context = (
            (group.title, PostViewTests.group.title),
            (group.slug, PostViewTests.group.slug),
            (group.description, PostViewTests.group.description)
        )
        self.check_context(context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url, _ = PostViewTests.templates_pages_names[2]
        response = self.authorized_client.get(url)
        context = (
            (response.context.get('user').username,
             PostViewTests.user.username),
        )
        self.check_context(context)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        url, _ = PostViewTests.templates_pages_names[3]
        response = self.authorized_client.get(url)
        context = (
            (response.context.get('post').text, PostViewTests.post.text),
            (response.context.get('post').author, PostViewTests.post.author),
            (
                str(response.context.get('post').comments.get(pk=1)),
                PostViewTests.comment.text[:15]
            ),
        )
        self.check_context(context)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        url, _ = PostViewTests.templates_pages_names[4]
        response = self.authorized_client.get(url)
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        )

        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        url, _ = PostViewTests.templates_pages_names[5]
        response = self.authorized_client.get(url)
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        )
        context = (
            (response.context.get('user').username,
             PostViewTests.user.username),
        )
        self.check_context(context)
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertTrue(response.context.get('is_edit'))

    def test_create_post_appear_in_index(self):
        url, _ = PostViewTests.templates_pages_names[0]
        response = self.authorized_client.get(url)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_create_post_appear_in_group_list(self):
        url, _ = PostViewTests.templates_pages_names[1]
        response = self.authorized_client.get(url)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_create_post_appear_in_profile(self):
        url, _ = PostViewTests.templates_pages_names[2]
        response = self.authorized_client.get(url)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_create_post_not_appear_in_group_list(self):
        """Пост не попадает в группу, для которой не предназначен."""
        self.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2'
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug2'}
        ))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_cache_index(self):
        """Кэширование шаблона index."""
        first = self.authorized_client.get(
            PostViewTests.templates_pages_names[0][0]
        )
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст поста'
        post.save()
        second = self.authorized_client.get(
            PostViewTests.templates_pages_names[0][0]
        )

        self.assertEqual(first.content, second.content)
        cache.clear()
        third = self.authorized_client.get(
            PostViewTests.templates_pages_names[0][0]
        )
        self.assertNotEqual(first.content, third.content)

    def test_follow_for_auth_user(self):
        """
        Авторизованный пользователь может подписываться
        на других пользователей.
        """
        user2 = User.objects.create_user(username='Follower')
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[user2])
        )
        self.assertEqual(Follow.objects.count(), 1)

    def test_content_for_follower_and_unfollow(self):
        """
        Подписанный юзер видит контент и отписывается.
        """
        user2 = User.objects.create_user(username='Follower')
        Post.objects.create(
            author=user2,
            text='Тестовый пост2',
        )
        follower = Follow.objects.create(
            user=PostViewTests.user,
            author=user2
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)
        follower.delete()
        response1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response.content, response1.content)

    def check_context(self, context):
        for response, expected in context:
            with self.subTest(response):
                self.assertEqual(response, expected)


class PaginatorViewsTest(TestCase):
    """Cоздаются фикстуры: клиент и 13 тестовых записей"""
    TEST_ENTRY = 13

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        list_posts = [Post(
            author=cls.user,
            text=f'Тестовый пост {i}',
            group=cls.group
        ) for i in range(cls.TEST_ENTRY)]
        Post.objects.bulk_create(list_posts)
        cls.page_names = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'}
            ),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_page_contains_thirteen_records(self):
        """
        Количество постов на первой странице равно 10.
        Количество постов на второй странице равно 3.
        """
        pages = (
            ('?page=1', 10),
            ('?page=2', 3),
        )
        for page_number, count_posts in pages:
            for page_name in self.page_names:
                with self.subTest(page_name=page_name):
                    response = self.authorized_client.get(
                        page_name + page_number
                    )
                    self.assertEqual(
                        len(response.context['page_obj']), count_posts
                    )
