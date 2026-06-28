import enum


class ImagePurpose(str, enum.Enum):
    PROFILE_IMAGE = "PROFILE_IMAGE"
    SOURCE = "SOURCE"
    PLACE = "PLACE"
    ETC = "ETC"
