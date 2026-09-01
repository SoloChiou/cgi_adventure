from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from game.models import Area, AreaEncounter, DropEntry, Item, Job, Monster


class SeedGameTests(TestCase):
    def test_seed_game_creates_sourced_chinese_ghost_literature_content_idempotently(self):
        call_command("seed_game", verbosity=0)
        call_command("seed_game", verbosity=0)

        self.assertEqual(Job.objects.filter(name="遊方客").count(), 1)
        area = Area.objects.get(name="蘭若古道")
        self.assertEqual(area.source_work, "《聊齋志異》")
        self.assertEqual(area.adaptation_type, Area.AdaptationType.ADAPTED)
        self.assertTrue(area.source_reference)
        self.assertTrue(area.lore_note)

        self.assertEqual(Monster.objects.count(), 3)
        self.assertEqual(set(area.encounters.values_list("monster__name", flat=True)), {"遊魂", "狐魅", "畫皮鬼"})
        self.assertEqual(AreaEncounter.objects.filter(area=area).count(), 3)
        self.assertEqual(Item.objects.count(), 4)
        self.assertEqual(DropEntry.objects.count(), 4)

        painted_skin = Monster.objects.get(name="畫皮鬼")
        self.assertEqual(painted_skin.source_work, "《聊齋志異》")
        self.assertEqual(painted_skin.source_reference, "〈畫皮〉")
        self.assertEqual(painted_skin.adaptation_type, Monster.AdaptationType.ADAPTED)
        self.assertTrue(painted_skin.lore_note)



class EnsureDevelopmentAdminTests(TestCase):
    @override_settings(DEBUG=True, DEV_ADMIN_USERNAME="test-admin", DEV_ADMIN_PASSWORD="Test-only@not-a-credential")
    def test_creates_superuser_with_configured_password(self):
        call_command("ensure_dev_admin", verbosity=0)
        user = get_user_model().objects.get(username="test-admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("Test-only@not-a-credential"))
