import enum


class RoomMemberRole(str, enum.Enum):
    HOST = "HOST"
    MEMBER = "MEMBER"
