import enum


class PlanStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    VOTING = "VOTING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
