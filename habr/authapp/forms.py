from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from authapp.models import User


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'ivanov2019'
        self.fields['email'].widget.attrs['placeholder'] = 'ivanov2019@gmail.com'
        self.fields['password1'].widget.attrs['placeholder'] = ' • • • • • • • • • •'
        self.fields['password2'].widget.attrs['placeholder'] = ' • • • • • • • • • •'
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['class'] = 'form-input'


class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'ivanov2019'
        self.fields['password'].widget.attrs['placeholder'] = ' • • • • • • • • • •'
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
