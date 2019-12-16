from django import forms

from .models import Comment


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )


class CommentForm(forms.ModelForm):
    class Meta:
        # Для создания формы из модели – указать, какую модель использовать в опциях класса Meta.
        # Каждое поле модели будет сопоставлено полю формы соответствующего типа.
        model = Comment

        # По умолчанию Django использует все поля модели.
        # Нужно явно указать какие поля использовать, а какие – нет.
        # Для этого достаточно определить списки fields или exclude соответственно.
        fields = ('name', 'email', 'body')


class SearchForm(forms.Form):
    query = forms.CharField()
