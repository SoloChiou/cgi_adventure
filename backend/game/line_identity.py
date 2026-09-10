import hashlib
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import ExternalIdentity, GameAccount


LINE_ID_TOKEN_VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"


class LineIdentityError(Exception):
    pass


@dataclass(frozen=True)
class VerifiedLineIdentity:
    user_id: str
    channel_id: str


def verify_line_id_token(id_token, channel_id, timeout=5):
    if not id_token or not channel_id:
        raise LineIdentityError("LINE 登入設定不完整。")

    request = Request(
        LINE_ID_TOKEN_VERIFY_URL,
        data=urlencode({"id_token": id_token, "client_id": channel_id}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise LineIdentityError("LINE 身分驗證失敗。") from error

    if payload.get("aud") != channel_id or not payload.get("sub"):
        raise LineIdentityError("LINE 身分驗證失敗。")
    return VerifiedLineIdentity(user_id=payload["sub"], channel_id=channel_id)


@transaction.atomic
def get_or_create_line_user(identity):
    external_identity = ExternalIdentity.objects.select_related("account__user").filter(
        provider="line",
        provider_user_id=identity.user_id,
        channel_context=identity.channel_id,
    ).first()
    if external_identity:
        account = external_identity.account
    else:
        digest = hashlib.sha256(
            "{}:{}".format(identity.channel_id, identity.user_id).encode()
        ).hexdigest()
        user, user_created = get_user_model().objects.get_or_create(username="line_{}".format(digest))
        if user_created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        account, _ = GameAccount.objects.get_or_create(user=user)
        ExternalIdentity.objects.create(
            account=account,
            provider="line",
            provider_user_id=identity.user_id,
            channel_context=identity.channel_id,
        )

    if account.status != GameAccount.Status.ACTIVE:
        raise LineIdentityError("此遊戲帳號目前無法登入。")
    account.last_login_at = timezone.now()
    account.save(update_fields=["last_login_at"])
    return account.user
