from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='Auth')
        cls.user2 = User.objects.create_user(username='Bob')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Тестовое описание группы не более 15 символов'
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

        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded,

        )

        Comment.objects.create(
            post=cls.post,
            author=cls.user2,
            text='Тестовый текст'
        )

    def setUp(self):
        # Гость
        self.guest_client = Client()
        # self.user = User.objects.create_user(username='Guest')
        # Авторизованный
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_show_correct_context(self):
        response = self.authorized_client.get(
            (reverse('posts:group_posts', kwargs={'slug': self.group.slug})))
        first_object_post = response.context['page_obj'][0]
        self.assertEqual(first_object_post.text, self.post.text)
        self.assertEqual(first_object_post.author, self.post.author)
        self.assertEqual(first_object_post.group, self.post.group)
        self.assertEqual(first_object_post.image, self.post.image)

        first_object_group = response.context['group']
        self.assertEqual(first_object_group.title,
                         self.group.title)
        self.assertEqual(first_object_group.description,
                         self.group.description)
        self.assertEqual(first_object_group.slug,
                         self.group.slug)

    def test_profile_list_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user}))
        first_object_author = response.context['author']
        self.assertEqual(first_object_author.username, self.user.username)

        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

        all_posts = response.context['total_posts']
        self.assertEqual(all_posts, self.user.posts.all().count())

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        one_post = response.context['post']
        self.assertEqual(one_post.text, self.post.text)
        self.assertEqual(one_post.author, self.post.author)
        self.assertEqual(one_post.group, self.post.group)
        self.assertEqual(one_post.image, self.post.image)

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        one_post = response.context['post']
        self.assertEqual(one_post.text, self.post.text)
        self.assertEqual(one_post.author, self.post.author)
        self.assertEqual(one_post.group, self.post.group)

        self.assertTrue(response.context.get('is_edit'))

    def test_post_appear(self):
        post_pages = (
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}))
        for page in post_pages:
            response = self.authorized_client.get(page)
            first_object_post = response.context['page_obj'][0]
            self.assertEqual(first_object_post.text, self.post.text)
            self.assertEqual(first_object_post.author, self.post.author)
            self.assertEqual(first_object_post.group, self.post.group)

    def test_auth_user_can_not_subscribe_on_yourself(self):
        response = self.authorized_client.post(
            f'/profile/{self.user.username}/follow/')
        self.assertRedirects(
            response, f'/profile/{self.user.username}/'
        )

    def test_auth_user_can_subscribe_and_unsubscribe_on_other_users(self):
        self.authorized_client.post(
            f'/profile/{self.user2.username}/follow/')
        count = Follow.objects.all().count()
        self.assertEqual(count, 1)
        self.authorized_client.post(
            f'/profile/{self.user2.username}/unfollow/')
        count2 = Follow.objects.all().count()
        self.assertEqual(count2, 0)

    def test_post_appears_in_subscribers(self):
        Follow.objects.create(user=self.user, author=self.user2)
        follow_index = self.authorized_client.get(reverse(
            'posts:follow_index'))
        self.assertIn(self.post.text, follow_index.content.decode())

    def test_post_not_appears_in_subscribers(self):
        follow_index = self.authorized_client.get(reverse(
            'posts:follow_index'))
        self.assertIn(self.post.text, follow_index.content.decode())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='Auth')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Тестовое описание группы не более 15 символов'
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

        number_of_posts = 13
        for post in range(number_of_posts):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group,
                image=uploaded

            )

    def setUp(self):
        # Гость
        self.guest_client = Client()
        # Авторизованный
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        posts_on_the_first_page = 10
        tested_pages = (
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        )
        for page in tested_pages:
            response = self.authorized_client.get(page)
            self.assertEqual(
                len(response.context['page_obj']), posts_on_the_first_page)

    def test_second_page_contains_three_records(self):
        posts_on_the_second_page = 3
        tested_pages = (
            reverse('posts:index') + '?page=2',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2',
        )
        for page in tested_pages:
            response = self.authorized_client.get(page)
            self.assertEqual(
                len(response.context['page_obj']), posts_on_the_second_page)

    def test_index_page_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Тест',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)
