from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from game.models import Area, GameAccount, Item, Job, Player, PlayerItem, Skill


class GameViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="hero", password="password")
        self.other_user = get_user_model().objects.create_user(username="other", password="password")
        self.job = Job.objects.create(name="初心者")
        self.account = GameAccount.objects.create(user=self.user)
        self.player = Player.objects.create(account=self.account, name="勇者", job=self.job)
        self.area = Area.objects.create(name="新手草原")
        self.client.force_login(self.user)

    def test_home_is_authenticated_and_shows_player(self):
        response = self.client.get(reverse("game:home"))
        self.assertContains(response, "勇者")
        self.client.logout()
        response = self.client.get(reverse("game:home"))
        self.assertRedirects(response, "{}?next=/".format(reverse("login")))

    def test_battle_endpoint_only_accepts_post(self):
        response = self.client.get(reverse("game:battle", args=[self.area.pk]))
        self.assertEqual(response.status_code, 405)

    def test_cannot_equip_another_players_item(self):
        other_account = GameAccount.objects.create(user=self.other_user)
        other_player = Player.objects.create(account=other_account, name="別人", job=self.job)
        item = Item.objects.create(name="別人的劍", item_type=Item.Type.WEAPON)
        row = PlayerItem.objects.create(player=other_player, item=item)
        response = self.client.post(reverse("game:equip", args=[row.pk]))
        self.assertEqual(response.status_code, 404)

    def test_leaderboard_order(self):
        other_account = GameAccount.objects.create(user=self.other_user)
        Player.objects.create(account=other_account, name="高手", job=self.job, job_count=1)
        response = self.client.get(reverse("game:leaderboard"))
        content = response.content.decode()
        self.assertLess(content.index("高手"), content.index("勇者"))

    @override_settings(DEBUG=False)
    def test_production_home_hides_level_simulation_area(self):
        Area.objects.create(name="等級模擬場", is_level_simulation=True)
        response = self.client.get(reverse("game:home"))
        self.assertNotContains(response, "等級模擬場")


class DevelopmentLoginTests(TestCase):
    @override_settings(DEBUG=True, DEV_ADMIN_USERNAME="test-admin", DEV_ADMIN_PASSWORD="Test-only@not-a-credential")
    def test_debug_login_prefills_development_credentials(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, 'value="test-admin"')
        self.assertContains(response, 'value="Test-only@not-a-credential"')

    @override_settings(DEBUG=False, DEV_ADMIN_USERNAME="test-admin", DEV_ADMIN_PASSWORD="Test-only@not-a-credential")
    def test_production_login_does_not_prefill_credentials(self):
        response = self.client.get(reverse("login"))
        self.assertNotContains(response, 'value="Test-only@not-a-credential"')


class JobProgressionViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="job-hero", password="password")
        account = GameAccount.objects.create(user=self.user)
        self.starter = Job.objects.create(name="遊方客", tier=Job.Tier.STARTER)
        self.first_jobs = [
            Job.objects.create(name=name, tier=Job.Tier.FIRST, required_level=5, prerequisite_job=self.starter)
            for name in ("金剛力士", "飛燕劍客", "御靈師", "方士")
        ]
        self.second = Job.objects.create(name="護法金剛", tier=Job.Tier.SECOND, required_level=25, prerequisite_job=self.first_jobs[0])
        self.player = Player.objects.create(account=account, name="轉職者", job=self.starter, level=5)
        self.client.force_login(self.user)

    def test_home_redirects_to_four_first_job_choices(self):
        response = self.client.get(reverse("game:home"))
        self.assertRedirects(response, reverse("game:job_progression"))
        response = self.client.get(reverse("game:job_progression"))
        for job in self.first_jobs:
            self.assertContains(response, job.name)

    def test_first_job_choice_transitions_and_shows_success(self):
        response = self.client.post(reverse("game:job_transition"), {"job_id": self.first_jobs[0].pk})
        self.assertContains(response, "轉職成功")
        self.player.refresh_from_db()
        self.assertEqual(self.player.job, self.first_jobs[0])

    def test_second_job_uses_automatic_transition_page(self):
        self.player.job = self.first_jobs[0]
        self.player.level = 25
        self.player.save(update_fields=["job", "level"])
        response = self.client.get(reverse("game:job_progression"))
        self.assertContains(response, "護法金剛")
        self.assertContains(response, "data-auto-submit")

    def test_cannot_submit_job_from_another_route(self):
        self.player.job = self.first_jobs[0]
        self.player.level = 25
        self.player.save(update_fields=["job", "level"])
        response = self.client.post(reverse("game:job_transition"), {"job_id": self.first_jobs[1].pk})
        self.assertRedirects(response, reverse("game:job_progression"))
        self.player.refresh_from_db()
        self.assertEqual(self.player.job, self.first_jobs[0])

    @override_settings(DEBUG=True)
    def test_debug_level_change_applies_stats_and_redirects_to_job_choice(self):
        response = self.client.post(reverse("game:development_set_level"), {
            "level": 5,
            "job": self.starter.pk,
            "hp": self.player.hp,
        })
        self.assertRedirects(response, reverse("game:job_progression"))

    @override_settings(DEBUG=True)
    def test_debug_controls_are_embedded_in_status_header(self):
        self.player.level = 1
        self.player.save(update_fields=["level"])
        response = self.client.get(reverse("game:home"))
        self.assertContains(response, "development-status-form")
        self.assertContains(response, 'name="job"')
        self.assertContains(response, 'name="level"')
        self.assertContains(response, 'class="development-resource"')
        self.assertNotContains(response, "LOCAL DEVELOPMENT")

    @override_settings(DEBUG=False)
    def test_production_cannot_change_level(self):
        response = self.client.post(reverse("game:development_set_level"), {"level": 25})
        self.assertEqual(response.status_code, 404)


class BattleResultTemplateTests(SimpleTestCase):
    def test_result_follows_events_without_round_headings(self):
        html = render_to_string("game/battle_result.html", {
            "battle": {
                "result": "win",
                "player_before": {"name": "勇者"},
                "monster_snapshot": {"name": "史萊姆"},
                "rounds": [{"round": 1, "events": [{
                    "actor_name": "勇者",
                    "target_name": "史萊姆",
                    "hit": True,
                    "critical": False,
                    "damage": 9,
                    "hp_before": 9,
                    "hp_after": 0,
                }]}],
                "rewards": {"exp": 45, "gold": 6, "proficiency": None, "drops": [], "level_ups": []},
                "battle_id": 1,
                "random_seed": 123,
            }
        })
        self.assertNotIn("Round 1", html)
        self.assertNotIn("result-banner", html)
        self.assertNotIn('class="panel rewards"', html)
        self.assertLess(html.index("造成 9 點傷害"), html.index("YOU WIN"))
        self.assertIn("battle_replay.js", html)

    def test_result_displays_skill_and_mp_cost(self):
        html = render_to_string("game/battle_result.html", {
            "battle": {
                "result": "win", "player_before": {"name": "術者"},
                "monster_snapshot": {"name": "妖物"},
                "rounds": [{"round": 1, "events": [{
                    "actor_name": "術者", "target_name": "妖物", "hit": True,
                    "critical": False, "damage": 20, "hp_before": 20, "hp_after": 0,
                    "skill_name": "火符咒", "mp_cost": 4, "mp_after": 6,
                }]}],
                "rewards": {"exp": 0, "gold": 0, "proficiency": None, "drops": [], "level_ups": []},
                "battle_id": 2, "random_seed": 456,
            }
        })
        self.assertIn("施放【火符咒】", html)
        self.assertIn("MP -4，剩餘 6", html)


class AutomaticJobSkillViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="skill-view", password="password")
        account = GameAccount.objects.create(user=self.user)
        self.job = Job.objects.create(name="測試方士", tier=Job.Tier.FIRST)
        self.player = Player.objects.create(account=account, name="術者", job=self.job)
        self.skills = [
            Skill.objects.create(job=self.job, name="技能{}".format(index), priority=index, mp_cost=1, damage_type="magical", power_multiplier=1.5, trigger_rate=1)
            for index in range(1, 4)
        ]
        self.client.force_login(self.user)

    def test_home_lists_current_job_skills(self):
        response = self.client.get(reverse("game:home"))
        self.assertContains(response, "自動技能")
        for skill in self.skills:
            self.assertContains(response, skill.name)

    def test_home_does_not_offer_manual_skill_configuration(self):
        response = self.client.get(reverse("game:home"))
        self.assertNotContains(response, "儲存技能配置")
        self.assertNotContains(response, "skills/configure")
