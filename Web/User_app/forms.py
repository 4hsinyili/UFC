from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms.fields import EmailField
from .models import CustomUser


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
            label="信箱",
            required=True,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
        )
    username = forms.CharField(
        label="使用者名稱",
        max_length=200,
        required=True,
        help_text='輸入姓名或其他希望被稱呼的方式',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '使用者名稱'}),
        )
    password1 = forms.CharField(
        label="密碼",
        required=True,
        help_text='密碼應為 8 個以上的英數混合字元',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密碼'}),
        )
    password2 = forms.CharField(
        label="確認密碼",
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '確認密碼'}),
        )

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'password1', 'password2']


class LoginForm(forms.Form):
    email = EmailField(
        label="信箱",
        widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(
        label="密碼",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': 
            "Please enter a correct email and password. Note that both fields may be case-sensitive.",
        'inactive': "This account is inactive.",
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Set the max length and label for the "username" field.
        self.username_field = CustomUser._meta.get_field(CustomUser.USERNAME_FIELD)
        username_max_length = self.username_field.max_length or 254
        self.fields['email'].max_length = username_max_length
        self.fields['email'].widget.attrs['maxlength'] = username_max_length

    def clean(self):
        username = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        return ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )
