from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from game.line_identity import LineIdentityError, VerifiedLineIdentity
from game.models import Area, BattleRecord, ExternalIdentity, GameAccount, Item, Job, Player, PlayerItem


class ApiFixture(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="hero")
        self.job = Job.objects.create(name="遊方客", tier=Job.Tier.STARTER)
        self.account = GameAccount.objects.create(user=self.user)
        self.player = Player.objects.create(account=self.account, name="勇者", job=self.job)
        self.area = Area.objects.create(name="新手草原")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


class AuthenticationApiTests(TestCase):
    @override_settings(LINE_CHANNEL_ID="123", CORS_ALLOWED_ORIGINS=["https://web.example"])
    @patch("game.views.verify_line_id_token")
    def test_line_login_creates_session_and_api_token(self, verify):
        verify.return_value = VerifiedLineIdentity(user_id="U123", channel_id="123")
        response = self.client.post(
            reverse("game:line_login"), {"id_token": "raw-token"},
            content_type="application/json", HTTP_ORIGIN="https://web.example",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertTrue(response.json()["api_token"])
        self.assertEqual(ExternalIdentity.objects.count(), 1)
        self.assertEqual(GameAccount.objects.count(), 1)

    @override_settings(LINE_CHANNEL_ID="mini", LINE_WEB_CHANNEL_ID="web", CORS_ALLOWED_ORIGINS=["https://web.example"])
    @patch("game.views.verify_line_id_token")
    def test_web_line_login_uses_web_channel(self, verify):
        verify.return_value = VerifiedLineIdentity(user_id="U123", channel_id="web")
        response = self.client.post(
            reverse("game:line_login"),
            {"id_token": "raw-token", "channel_context": "web"},
            content_type="application/json",
            HTTP_ORIGIN="https://web.example",
        )
        self.assertEqual(response.status_code, 200)
        verify.assert_called_once_with("raw-token", "web")

    @override_settings(LINE_CHANNEL_ID="mini", LINE_WEB_CHANNEL_ID="web", CORS_ALLOWED_ORIGINS=["https://web.example"])
    @patch("game.views.verify_line_id_token")
    def test_unknown_line_login_context_is_rejected(self, verify):
        response = self.client.post(
            reverse("game:line_login"),
            {"id_token": "raw-token", "channel_context": "unknown"},
            content_type="application/json",
            HTTP_ORIGIN="https://web.example",
        )
        self.assertEqual(response.status_code, 400)
        verify.assert_not_called()

    @override_settings(LINE_CHANNEL_ID="123", CORS_ALLOWED_ORIGINS=["https://web.example"])
    def test_line_login_rejects_untrusted_or_missing_origin(self):
        for origin in (None, "https://evil.example"):
            headers = {"HTTP_ORIGIN": origin} if origin else {}
            response = self.client.post(reverse("game:line_login"), {"id_token": "token"}, content_type="application/json", **headers)
            self.assertEqual(response.status_code, 403)

    @override_settings(LINE_CHANNEL_ID="123", CORS_ALLOWED_ORIGINS=["https://web.example"])
    @patch("game.views.verify_line_id_token", side_effect=LineIdentityError("invalid"))
    def test_invalid_line_token_is_rejected(self, verify):
        response = self.client.post(reverse("game:line_login"), {"id_token": "bad"}, content_type="application/json", HTTP_ORIGIN="https://web.example")
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_protected_api_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("game:game_state")).status_code, 401)

    def test_logout_revokes_api_token(self):
        user = get_user_model().objects.create_user(username="logout")
        token = Token.objects.create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self.assertEqual(client.post(reverse("game:logout")).status_code, 200)
        self.assertFalse(Token.objects.filter(pk=token.key).exists())


class GameApiTests(ApiFixture):
    def test_game_state_returns_player_and_hides_simulation_in_production(self):
        Area.objects.create(name="等級模擬場", is_level_simulation=True)
        with override_settings(DEBUG=False):
            response = self.client.get(reverse("game:game_state"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["player"]["name"], "勇者")
        self.assertNotIn("等級模擬場", [row["name"] for row in response.json()["areas"]])

    def test_create_player_validates_name_and_creates_equipment(self):
        user = get_user_model().objects.create_user(username="new")
        GameAccount.objects.create(user=user)
        client = APIClient()
        client.force_authenticate(user)
        response = client.post(reverse("game:create_player"), {"name": " 新人 "}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "新人")
        self.assertTrue(Player.objects.get(account__user=user).equipment)

    def test_cannot_equip_another_players_item(self):
        other = get_user_model().objects.create_user(username="other")
        other_account = GameAccount.objects.create(user=other)
        other_player = Player.objects.create(account=other_account, name="別人", job=self.job)
        item = Item.objects.create(name="別人的劍", item_type=Item.Type.WEAPON)
        row = PlayerItem.objects.create(player=other_player, item=item)
        self.assertEqual(self.client.post(reverse("game:equip", args=[row.pk])).status_code, 404)

    def test_leaderboard_is_ordered(self):
        other = get_user_model().objects.create_user(username="expert")
        account = GameAccount.objects.create(user=other)
        Player.objects.create(account=account, name="高手", job=self.job, job_count=1)
        response = self.client.get(reverse("game:leaderboard"))
        self.assertEqual(response.json()[0]["name"], "高手")

    def test_battle_endpoint_only_accepts_post(self):
        self.assertEqual(self.client.get(reverse("game:battle", args=[self.area.pk])).status_code, 405)

    def test_battle_history_is_owner_only(self):
        record = BattleRecord.objects.create(player=self.player, monster_snapshot={"name": "妖物"}, result="win", end_reason="monster_dead", rounds=[], rewards={}, random_seed=42)
        self.assertEqual(self.client.get(reverse("game:battle_history", args=[record.pk])).status_code, 200)
        other = get_user_model().objects.create_user(username="other-history")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(reverse("game:battle_history", args=[record.pk])).status_code, 404)


class JobApiTests(ApiFixture):
    def test_transition_only_accepts_available_job(self):
        target = Job.objects.create(name="金剛力士", tier=Job.Tier.FIRST, required_level=5, prerequisite_job=self.job)
        self.player.level = 5
        self.player.save(update_fields=["level"])
        response = self.client.post(reverse("game:job_transition"), {"job_id": target.pk}, format="json")
        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertEqual(self.player.job, target)

    @override_settings(DEBUG=False)
    def test_development_player_endpoint_is_disabled_in_production(self):
        response = self.client.patch(reverse("game:development_player"), {"level": 25}, format="json")
        self.assertEqual(response.status_code, 404)


class HealthApiTests(TestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse("game:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
