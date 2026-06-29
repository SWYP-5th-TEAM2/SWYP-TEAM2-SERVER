from uuid import UUID

from app.schemas.common import CamelModel


class CreateRoomResponse(CamelModel):
    room_id: UUID
    invite_code: str


class InviteCodeResponse(CamelModel):
    invite_code: str


class JoinRoomResponse(CamelModel):
    room_id: UUID


class RoomMemberResponse(CamelModel):
    user_id: UUID
    profile_image: str | None
    nickname: str | None
    role: str


class RoomDetailResponse(CamelModel):
    room_id: UUID
    room_name: str
    member_count: int
    place_count: int
    members: list[RoomMemberResponse]


class MyRoomSummaryResponse(CamelModel):
    room_id: UUID
    room_name: str
    color: str
    member_count: int
    member_preview_names: list[str]
    plan_status: str | None
    vote_member_count: int


class MyRoomsResponse(CamelModel):
    rooms: list[MyRoomSummaryResponse]
