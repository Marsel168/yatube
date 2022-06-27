import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from ..models import Post, Group, Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
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
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': 'HasNoName'}
        ))
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(str(post.author), 'HasNoName')
        self.assertEqual(str(post.text), 'Тестовый текст')
        self.assertEqual(str(post.image), 'posts/small.gif')

    def test_create_post_anonymous(self):
        """Работа форм create_post с анонимным пользователем."""
        self.guest_client = Client()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        create_url = reverse('posts:post_create')
        self.assertRedirects(response, f'{login_url}?next={create_url}')
        self.assertEqual(Post.objects.count(), 0)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост'
        )
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст изменен',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': '1'}
        ))
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(str(post.author), 'HasNoName')
        self.assertEqual(str(post.text), 'Тестовый текст изменен')

    def test_edit_post_anonymous(self):
        """Работа форм edit_post с анонимным пользователем."""
        self.guest_client = Client()
        form_data = {
            'author': self.user,
            'text': 'Тестовый текст изменен',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        create_url = reverse('posts:post_create')
        self.assertRedirects(response, f'{login_url}?next={create_url}')
        self.assertEqual(Post.objects.count(), 0)

    def test_add_comment(self):
        """Валидная форма add_comment создает комментарий."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        form_data = {
            'author': self.user,
            'post': post,
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': '1'}
        ))
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(str(comment.text), 'Тестовый комментарий')
        
    def test_add_comment_anonymous(self):
        """Работа формы comment с анонимным пользователем."""
        self.guest_client = Client()
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        form_data = {
            'author': self.user,
            'post': post,
            'text': 'Тестовый комментарий'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True
        )
        login_url = reverse('users:login')
        comment_url = reverse('posts:add_comment', kwargs={'post_id': '1'})
        self.assertRedirects(response, f'{login_url}?next={comment_url}')
        self.assertEqual(Comment.objects.count(), 0)
        