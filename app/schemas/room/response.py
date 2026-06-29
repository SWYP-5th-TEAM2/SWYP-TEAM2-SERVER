from uuid import UUID

from app.schemas.common import CamelModel


class CreateRoomResponse(CamelModel):
    room_id: UUID
    invite_code: str


class InviteCodeResponse(CamelModel):
    invite_code: str


class JoinRoomResponse(CamelModel):
    room_id: UUID
