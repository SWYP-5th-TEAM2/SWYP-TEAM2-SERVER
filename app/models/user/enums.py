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

class WithdrawalReason(str, enum.Enum):
    RARELY_USE = "RARELY_USE" # 자주 이용하지 않아요
    MISSING_FEATURES = "MISSING_FEATURES" # 원하는 기능이 없어요
    DIFFICULT_TO_USE = "DIFFICULT_TO_USE" # 서비스 이용이 불편해요
    NO_TIME_TO_USE = "NO_TIME_TO_USE" # 이용할 시간이 없어요
    ETC = "ETC" # 기타
