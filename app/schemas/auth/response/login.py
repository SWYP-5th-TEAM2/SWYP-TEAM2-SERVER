from app.schemas.common import CamelModel


class LoginResponse(CamelModel):
    access_token: str
    refresh_token: str
    expires_in: int
    is_new_user: bool