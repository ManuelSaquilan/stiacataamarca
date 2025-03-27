from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser, Comercio

class CustomUserCreationForm(UserCreationForm):
    comercio = forms.ModelChoiceField(queryset=Comercio.objects.filter(activo=True), required=False, label="Comercio")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'comercio']


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

