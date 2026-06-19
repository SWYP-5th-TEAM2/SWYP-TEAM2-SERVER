from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core.exceptions import SocialLoginFailedException, BlockedUserException
from app.core.security.jwt import create_tokens, decode_refresh_token, get_subject, get_session_id, get_jti
from app.core.security.token_store import save_refresh_session
from app.models.user.enums import Provider, UserAccountStatus
from app.repository.user import find_user_by_provider, create_user
from app.schemas.auth import LoginResponse
from app.services.auth.oauth.factory import get_oauth_client


async def social_login(
    db: Session,
    redis: Redis,
    *,
    provider: Provider,
    code: str,
) -> LoginResponse:
    oauth_client = get_oauth_client(provider)

    oauth_user_info = await oauth_client.authenticate(code)

    if oauth_user_info.provider != provider:
        raise SocialLoginFailedException()

    user = find_user_by_provider(
        db=db,
        provider=provider,
        provider_id=oauth_user_info.provider_id,
    )

    is_new_user = False

    if user is None:
        user = create_user(
            db=db,
            provider=provider,
            provider_id=oauth_user_info.provider_id,
            email=oauth_user_info.email,
            nickname=oauth_user_info.nickname
        )
        db.commit()
        db.refresh(user)
        is_new_user = True

    if user.status == UserAccountStatus.BLOCKED:
        raise BlockedUserException()

    tokens = create_tokens(user.id)

    refresh_payload = decode_refresh_token(tokens.refresh_token)
    refresh_user_id = get_subject(refresh_payload)
    session_id = get_session_id(refresh_payload)
    refresh_jti = get_jti(refresh_payload)

    await save_refresh_session(
        redis=redis,
        session_id=session_id,
        user_id=refresh_user_id,
        current_jti=refresh_jti,
    )

    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        is_new_user=is_new_user,
    )