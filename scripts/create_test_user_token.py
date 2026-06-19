from uuid import uuid4

from app.config import settings
from app.core.security.jwt import create_tokens
from app.database.session import SessionLocal
from app.models.user.enums import Provider, UserAccountStatus, UserRole
from app.models.user.user import User
from app.repository.user import find_user_by_provider


TEST_ID = uuid4().hex[:8]

PROVIDER = Provider.KAKAO
PROVIDER_ID = f"cli-test-user-{TEST_ID}"
EMAIL = f"cli-test-{TEST_ID}@example.com"
NICKNAME = "CLI테스트유저"


def main() -> None:
    if settings.app_env == "prod":
        raise RuntimeError("운영 환경에서는 테스트 유저 생성 스크립트를 실행할 수 없습니다.")

    db = SessionLocal()

    try:
        user = find_user_by_provider(
            db=db,
            provider=PROVIDER,
            provider_id=PROVIDER_ID,
        )

        is_new_user = False

        if user is None:
            user = User(
                provider=PROVIDER,
                provider_id=PROVIDER_ID,
                email=EMAIL,
                nickname=NICKNAME,
                role=UserRole.USER,
                status=UserAccountStatus.ACTIVE,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            is_new_user = True

        tokens = create_tokens(user.id)

        print("\n=== 테스트 유저 토큰 발급 완료 ===")
        print(f"is_new_user: {is_new_user}")
        print(f"user_id: {user.id}")
        print(f"provider: {user.provider.value}")
        print(f"provider_id: {user.provider_id}")
        print(f"email: {user.email}")
        print(f"nickname: {user.nickname}")

        print("\naccessToken:")
        print(tokens.access_token)

        print("\nrefreshToken:")
        print(tokens.refresh_token)

        print(f"\nexpiresIn: {tokens.expires_in}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()