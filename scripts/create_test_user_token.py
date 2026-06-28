# 실행 명령어: python -m scripts.create_test_user_token

import asyncio
from uuid import uuid4

from app.config import settings
from app.core.redis import close_redis, connect_redis, get_redis
from app.core.security.jwt import (
    create_tokens,
    decode_refresh_token,
    get_jti,
    get_session_id,
    get_subject,
)
from app.core.security.token_store import save_refresh_session
from app.database.session import SessionLocal
from app.models.user.enums import Provider
from app.repository.user import create_user


async def main() -> None:
    if settings.app_env.lower() in {"prod", "production"}:
        raise RuntimeError(
            "운영 환경에서는 테스트 유저 생성 스크립트를 실행할 수 없습니다.",
        )

    test_id = uuid4().hex[:8]
    provider_id = f"cli-test-user-{test_id}"
    email = f"cli-test-{test_id}@example.com"
    nickname = "CLI테스트유저"

    await connect_redis()
    db = SessionLocal()

    try:
        # 소셜 인증 없이 항상 새로운 활성 테스트 사용자를 생성한다.
        user = create_user(
            db=db,
            provider=Provider.KAKAO,
            provider_id=provider_id,
            email=email,
            nickname=nickname,
        )
        db.commit()
        db.refresh(user)

        # 실제 로그인과 동일하게 JWT를 발급하고 refresh session을 Redis에 저장한다.
        tokens = create_tokens(user.id)
        refresh_payload = decode_refresh_token(tokens.refresh_token)
        refresh_user_id = get_subject(refresh_payload)
        session_id = get_session_id(refresh_payload)
        refresh_jti = get_jti(refresh_payload)

        await save_refresh_session(
            redis=get_redis(),
            session_id=session_id,
            user_id=refresh_user_id,
            current_jti=refresh_jti,
        )

        print("\n=== 테스트 유저 및 토큰 생성 완료 ===")
        print(f"user_id: {user.id}")
        print(f"provider: {user.provider.value}")
        print(f"provider_id: {user.provider_id}")
        print(f"email: {user.email}")
        print(f"nickname: {user.nickname}")

        print("\naccessToken:")
        print(tokens.access_token)

        print("\nrefreshToken:")
        print(tokens.refresh_token)

        print(f"\nexpiresIn: {tokens.expires_in}")
        print("\nAuthorization 헤더:")
        print(f"Bearer {tokens.access_token}\n")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())
