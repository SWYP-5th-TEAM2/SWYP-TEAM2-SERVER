from app.core.exceptions import UnsupportedProviderException
from app.models.user.enums import Provider
from app.services.auth.oauth.apple_client import AppleOAuthClient
from app.services.auth.oauth.base import OAuthClient
from app.services.auth.oauth.google_client import GoogleOAuthClient
from app.services.auth.oauth.kakao_client import KakaoOAuthClient


def get_oauth_client(provider: Provider) -> OAuthClient:
    # 카카오 소셜 인증
    if provider == Provider.KAKAO:
        return KakaoOAuthClient()

    # 구글 소셜 인증
    if provider == Provider.GOOGLE:
        return GoogleOAuthClient()

    # 애플 소셜 인증
    if provider == Provider.APPLE:
        return AppleOAuthClient()

    raise UnsupportedProviderException()