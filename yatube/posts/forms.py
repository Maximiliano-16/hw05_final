from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
        }
        help_texts = {
            'text': 'Текст поста',
            'group': 'Группа, к которой принадлежит пост',
        }

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == "":
            raise forms.ValidationError('Нельзя создать пост с пустым полем')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
