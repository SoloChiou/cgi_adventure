from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "僅在 DEBUG 模式依環境變數建立或更新本機開發管理員"

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("ensure_dev_admin 只能在 DEBUG=True 時執行。")
        username = settings.DEV_ADMIN_USERNAME
        password = settings.DEV_ADMIN_PASSWORD
        if not username or not password:
            raise CommandError("必須設定 DEV_ADMIN_USERNAME 與 DEV_ADMIN_PASSWORD。")
        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        action = "建立" if created else "更新"
        self.stdout.write(self.style.SUCCESS("已{}本機開發管理員：{}".format(action, username)))
