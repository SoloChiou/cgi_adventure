from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from game.models import Area, GameAccount, Item, Job, Player, PlayerItem


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
