from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image', 'video']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'add-post',
                'placeholder': 'What is in your mind?',
                'rows': 3
            }),
            'image': forms.FileInput(attrs={
                'class': 'add-img',
                'id': 'add-img',
                'accept': 'image/*'
            }),
            'video': forms.FileInput(attrs={
                'class': 'add-video',
                'id': 'add-video',
                'accept': 'video/*'
            })
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'comment-input',
                'placeholder': 'Write a comment...'
            })
        }
