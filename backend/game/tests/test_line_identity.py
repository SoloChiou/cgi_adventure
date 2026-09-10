import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from game.line_identity import LineIdentityError, verify_line_id_token


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
