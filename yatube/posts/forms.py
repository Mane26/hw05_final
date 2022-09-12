from django import forms
from django.forms import ModelForm

from .models import Comment, Follow, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст подсказки',
            'group': 'Группа'
        }

    def clean_group(self):
        return self.cleaned_data['group']


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class FollowForm(ModelForm):
    class Meta:
        model = Follow
        labels = {'user': 'Подписка на:', 'author': 'Автор записи'}
        fields = ['user']
