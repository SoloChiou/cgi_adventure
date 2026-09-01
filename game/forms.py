from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Job, Player


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


class DevelopmentPlayerForm(forms.Form):
    level = forms.IntegerField(label="角色等級", min_value=1, max_value=99)
    job = forms.ModelChoiceField(label="職業", queryset=Job.objects.none())
    hp = forms.IntegerField(label="目前 HP", min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["job"].queryset = Job.objects.filter(enabled=True).order_by("tier", "id")
