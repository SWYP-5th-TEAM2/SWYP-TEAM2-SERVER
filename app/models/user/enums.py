import enum


class Provider(str, enum.Enum):
    KAKAO = "KAKAO"
    GOOGLE = "GOOGLE"
    APPLE = "APPLE"


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserAccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE" # 활성
    INACTIVE = "INACTIVE" # 비활성
    BLOCKED = "BLOCKED" # 정지
    WITHDRAWN = "WITHDRAWN" # 탈퇴
