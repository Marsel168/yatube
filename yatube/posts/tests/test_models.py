from django.test import TestCase
from ..models import Post, Group, Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост. Тестовый пост'
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        expected_model_display = (
            (str(post), post.text[:15]),
            (str(group), f'Группа - "{group.title}"'),
            (str(comment), comment.text[:15])
        )
        for model, expected in expected_model_display:
            with self.subTest(model=model):
                self.assertEqual(expected, model)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = (
            ('text', 'Текст'),
            ('author', 'Автор'),
            ('image', 'Картинка')
        )

        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

        group = PostModelTest.group
        field_verboses = (
            ('title', 'Имя'),
            ('slug', 'Адрес'),
            ('description', 'Описание')
        )

        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )
        
        comment = PostModelTest.comment
        field_verboses = (
            ('text', 'Комментарий'),
        )

        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, expected_value
                )
