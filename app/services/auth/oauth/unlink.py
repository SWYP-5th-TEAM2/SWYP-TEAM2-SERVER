from app.models.user.enums import Provider


async def unlink_kakao_account(provider_id: str) -> None:
    # TODO: Kakao 연결 끊기 API 호출 비즈니스 로직 구현
    pass


async def unlink_google_account(provider_id: str) -> None:
    # TODO: Google 연결 끊기 API 호출 비즈니스 로직 구현
    pass


async def unlink_apple_account(provider_id: str) -> None:
    # TODO: Apple 연결 끊기 API 호출 비즈니스 로직 구현
    pass


async def unlink_social_account(
    *,
    provider: Provider,
    provider_id: str,
) -> None:
    if provider == Provider.KAKAO:
        await unlink_kakao_account(provider_id)
        return

    if provider == Provider.GOOGLE:
        await unlink_google_account(provider_id)
        return

    if provider == Provider.APPLE:
        await unlink_apple_account(provider_id)
