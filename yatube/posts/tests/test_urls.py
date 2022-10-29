from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author_post')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы не более 15 символов'
        )

        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group

        )

    def setUp(self):
        # Гость
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Guest')
        # Авторизованный
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Автор
        self.author_client = Client()
        self.author_user = PostURLTests.user
        self.author_client.force_login(self.author_user)

    def test_public_urls_guest(self):
        post_id = self.post.id
        urls_exists = {
            self.guest_client.get('/'): HTTPStatus.OK,
            self.guest_client.get('/group/test-slug/'): HTTPStatus.OK,
            self.guest_client.get
            (f'/profile/{self.user.username}/'): HTTPStatus.OK,
            self.guest_client.get(f'/posts/{post_id}/'): HTTPStatus.OK,
            self.guest_client.get('/unexisting_page/'): HTTPStatus.NOT_FOUND,
            self.authorized_client.get('/create/'): HTTPStatus.OK,
            self.author_client.get(f'/posts/{post_id}/edit/'): HTTPStatus.OK,
            self.authorized_client.get('/follow/'): HTTPStatus.OK,

        }
        for address, answer in urls_exists.items():
            with self.subTest(address=address):
                self.assertEqual(address.status_code, answer)

    def test_post_edit_urls_guest(self):
        post_id = self.post.id
        response = self.guest_client.get(
            f'/posts/{post_id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post_id}/edit/'
        )

    def test_post_comment_urls_guest(self):
        post_id = self.post.id
        response = self.guest_client.get(
            f'/posts/{post_id}/comment/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{post_id}/comment/'
        )

    def test_post_create_urls_guest(self):
        response = self.guest_client.get(
            '/create/', follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_urls_auth(self):
        post_id = self.post.id
        response = self.authorized_client.get(
            f'/posts/{post_id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{post_id}/'
        )

    def test_urls_uses_correct_template(self):
        post_id = self.post.id
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/Guest/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_custom_template_errors(self):
        templates_url_names = {
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                respone = self.guest_client.get(address)
                self.assertTemplateUsed(respone, template)


class StaticURLTests(TestCase):
    def test_homepage(self):
        # Создаем экземпляр клиента
        guest_client = Client()
        # Делаем запрос к главной странице и проверяем статус
        response = guest_client.get('/')
        # Утверждаем, что для прохождения теста код должен быть равен 200
        self.assertEqual(response.status_code, 200)
