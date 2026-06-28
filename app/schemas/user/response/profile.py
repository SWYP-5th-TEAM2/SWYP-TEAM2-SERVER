from uuid import UUID

from app.schemas.common import CamelModel


class UpdateUserProfileResponse(CamelModel):
    nickname: str
    profile_image_url: str | None


class MyRoomResponse(CamelModel):
    room_id: UUID
    room_name: str
    member_count: int


class UserProfileResponse(CamelModel):
    nickname: str | None
    profile_image: str | None
    email: str | None
    my_rooms: list[MyRoomResponse]
    recurring_schedule_count: int
