from app.schemas.common import CamelModel


class TokenResponse(CamelModel):
    access_token: str
    refresh_token: str
    expires_in: int
