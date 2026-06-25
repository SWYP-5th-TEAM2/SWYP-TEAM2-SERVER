import enum


class NotificationType(str, enum.Enum):
    PLAN_REQUESTED = "PLAN_REQUESTED"
    PLAN_CONFIRMED = "PLAN_CONFIRMED"
    MEMBER_GOING = "MEMBER_GOING"
    QUIET_RECOMMENDATION = "QUIET_RECOMMENDATION"
    RESPONSE_DEADLINE_SOON = "RESPONSE_DEADLINE_SOON"


class NotificationTargetType(str, enum.Enum):
    PLAN = "PLAN"
    ROOM = "ROOM"
    PLACE = "PLACE"


class NotificationViewType(str, enum.Enum):
    RESPONSE = "RESPONSE"
    STATUS = "STATUS"
    TICKET = "TICKET"
    PLACE_LIST = "PLACE_LIST"
    DRAW = "DRAW"
