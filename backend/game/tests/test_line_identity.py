import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase

from game.line_identity import LineIdentityError, VerifiedLineIdentity, get_or_create_line_user, verify_line_id_token
from game.models import ExternalIdentity, GameAccount


class LineIdentityVerificationTests(SimpleTestCase):
    @patch("game.line_identity.urlopen")
    def test_valid_id_token_returns_verified_identity(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({"sub": "U123", "aud": "123"}).encode()
        urlopen.return_value.__enter__.return_value = response

        identity = verify_line_id_token("raw-token", "123")

        self.assertEqual(identity.user_id, "U123")
        self.assertEqual(identity.channel_id, "123")
        request = urlopen.call_args.args[0]
        self.assertNotIn("raw-token", request.full_url)

    @patch("game.line_identity.urlopen")
    def test_wrong_channel_is_rejected(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({"sub": "U123", "aud": "wrong"}).encode()
        urlopen.return_value.__enter__.return_value = response

        with self.assertRaises(LineIdentityError):
            verify_line_id_token("raw-token", "123")

    def test_missing_configuration_is_rejected_without_request(self):
        with self.assertRaises(LineIdentityError):
            verify_line_id_token("raw-token", "")


class LineAccountTests(TestCase):
    def test_same_provider_user_reuses_account_across_channels(self):
        mini_user = get_or_create_line_user(VerifiedLineIdentity(user_id="U123", channel_id="mini"))
        web_user = get_or_create_line_user(VerifiedLineIdentity(user_id="U123", channel_id="web"))

        self.assertEqual(web_user.pk, mini_user.pk)
        self.assertEqual(GameAccount.objects.count(), 1)
        self.assertEqual(ExternalIdentity.objects.count(), 2)
