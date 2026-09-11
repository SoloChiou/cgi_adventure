from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from game.models import Area, AreaEncounter, DropEntry, GameAccount, Item, Job, JobTitle, Monster, Player, Skill


class SeedGameTests(TestCase):
    def test_seed_game_creates_sourced_chinese_ghost_literature_content_idempotently(self):
        call_command("seed_game", verbosity=0)
        call_command("seed_game", verbosity=0)

        self.assertEqual(Job.objects.filter(name="遊方客").count(), 1)
        self.assertEqual(Job.objects.count(), 15)
        self.assertEqual(Job.objects.filter(enabled=True, tier=Job.Tier.FIRST).count(), 14)
        self.assertEqual(Job.objects.get(name="武者").required_strength, 12)
        self.assertEqual(Job.objects.get(name="通靈者").required_intellect, 14)
        self.assertEqual(Job.objects.get(name="影衛").required_speed, 12)
        self.assertEqual(Job.objects.get(name="劍客").allowed_weapon_types, ["劍"])
        self.assertEqual(JobTitle.objects.count(), 98)
        warrior_titles = list(JobTitle.objects.filter(job__name="武者").values_list("rank", "min_level", "max_level", "name", "name_en"))
        self.assertEqual(warrior_titles[0], (1, 1, 6, "習武人", "Martial Initiate"))
        self.assertEqual(warrior_titles[-1], (7, 42, 99, "蕩魔武聖", "Demon-Quelling War Saint"))
        self.assertEqual(Skill.objects.filter(enabled=True).count(), 14)
        self.assertEqual(Job.objects.get(name="法主").skills.get(enabled=True).name, "萬法歸一")
        self.assertEqual(Skill.objects.get(name="萬法歸一").name_en, "Convergence of All Arts")
        area = Area.objects.get(name="蘭若古道")
        self.assertEqual(area.source_work, "《聊齋志異》")
        self.assertEqual(area.adaptation_type, Area.AdaptationType.ADAPTED)
        self.assertTrue(area.source_reference)
        self.assertTrue(area.lore_note)

        self.assertEqual(Monster.objects.count(), 4)
        self.assertEqual(set(area.encounters.values_list("monster__name", flat=True)), {"遊魂", "狐魅", "畫皮鬼"})
        self.assertEqual(AreaEncounter.objects.filter(area=area).count(), 3)
        self.assertEqual(Item.objects.count(), 4)
        self.assertEqual(DropEntry.objects.count(), 4)

        simulation_area = Area.objects.get(name="等級模擬場")
        self.assertTrue(simulation_area.is_level_simulation)
        self.assertEqual(simulation_area.encounters.get().monster.name, "修行幻影")

        painted_skin = Monster.objects.get(name="畫皮鬼")
        self.assertEqual(painted_skin.source_work, "《聊齋志異》")
        self.assertEqual(painted_skin.source_reference, "〈畫皮〉")
        self.assertEqual(painted_skin.adaptation_type, Monster.AdaptationType.ADAPTED)
        self.assertTrue(painted_skin.lore_note)

    def test_seed_game_maps_legacy_spirit_job_to_spirit_medium(self):
        legacy = Job.objects.create(name="御靈師", tier=Job.Tier.FIRST)
        user = get_user_model().objects.create_user(username="legacy-player")
        player = Player.objects.create(account=GameAccount.objects.create(user=user), name="舊角色", job=legacy)

        call_command("seed_game", verbosity=0)

        player.refresh_from_db()
        legacy.refresh_from_db()
        self.assertEqual(player.job.name, "通靈者")
        self.assertFalse(legacy.enabled)



class EnsureDevelopmentAdminTests(TestCase):
    @override_settings(DEBUG=True, DEV_ADMIN_USERNAME="test-admin", DEV_ADMIN_PASSWORD="Test-only@not-a-credential")
    def test_creates_superuser_with_configured_password(self):
        call_command("ensure_dev_admin", verbosity=0)
        user = get_user_model().objects.get(username="test-admin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("Test-only@not-a-credential"))
