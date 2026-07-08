import enum


class RoomMemberRole(str, enum.Enum):
    HOST = "HOST"
    MEMBER = "MEMBER"


class RoomMemberLeftReason(str, enum.Enum):
    LEFT = "LEFT"
    KICKED = "KICKED"
