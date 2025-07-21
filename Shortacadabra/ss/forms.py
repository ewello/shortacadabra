from django import forms
from .models import Url, User
# from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm

class UrlForm(forms.ModelForm):
    class Meta():
        model = Url
        fields = ['url']


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    saveSession = forms.BooleanField(required=False)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")