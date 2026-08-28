from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Player


class DevelopmentAuthenticationForm(AuthenticationForm):
    password = forms.CharField(
        label="密碼",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}, render_value=True),
    )


class PlayerCreateForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ["name"]
        labels = {"name": "角色名稱"}

    def clean_name(self):
        return self.cleaned_data["name"].strip()
