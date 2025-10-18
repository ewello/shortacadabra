from django import forms
from .models import Url, User, CustomDomain
# from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm

class UrlForm(forms.ModelForm):
    class Meta():
        model = Url
        fields = ['url', 'custom_domain']
        widgets = {
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'custom_domain': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['custom_domain'].queryset = CustomDomain.objects.filter(
                user=user, 
                is_active=True
            )
            self.fields['custom_domain'].empty_label = "Использовать стандартный домен"
            self.fields['custom_domain'].required = False
        else:
            self.fields['custom_domain'].queryset = CustomDomain.objects.none()
            self.fields['custom_domain'].widget = forms.HiddenInput()


class CustomDomainForm(forms.ModelForm):
    class Meta:
        model = CustomDomain
        fields = ['domain']
        widgets = {
            'domain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'example.com'
            })
        }
    
    def clean_domain(self):
        domain = self.cleaned_data.get('domain')
        if domain:
            # Remove protocol if present
            domain = domain.replace('https://', '').replace('http://', '')
            # Remove trailing slash
            domain = domain.rstrip('/')
        return domain


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    saveSession = forms.BooleanField(required=False)
    hp = forms.CharField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_hp(self):
        if self.cleaned_data.get('hp'):
            raise forms.ValidationError("Spam detected")
        return ""