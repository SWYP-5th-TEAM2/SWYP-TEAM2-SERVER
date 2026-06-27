import enum


class PlaceStatus(str, enum.Enum):
    READY_TO_DRAW = "READY_TO_DRAW"
    NEEDS_EDIT = "NEEDS_EDIT"
