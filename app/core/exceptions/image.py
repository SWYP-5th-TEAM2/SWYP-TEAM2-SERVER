from app.core.exceptions.common import (
    BadGatewayException,
    BadRequestException,
    InternalServerException,
    ServiceUnavailableException,
)


class FileMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="FILE_MISSING",
            message="이미지 파일은 필수입니다.",
        )

class ImagePurposeMissingException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="IMAGE_PURPOSE_MISSING",
            message="이미지 사용 목적은 필수입니다.",
        )

class UnsupportedImagePurposeException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
           code="UNSUPPORTED_IMAGE_PURPOSE",
            message="지원하지 않는 이미지 사용 목적입니다.",
        )

class UnsupportedImageFormatException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_IMAGE_FORMAT",
            message="지원하지 않는 이미지 형식입니다.",
        )

class UnsupportedImageSizeException(BadRequestException):
    def __init__(self) -> None:
        super().__init__(
            code="UNSUPPORTED_IMAGE_SIZE",
            message="이미지 파일 최대 크기를 초과했습니다.",
        )

class ImageUploadFailedException(InternalServerException):
    def __init__(self) -> None:
        super().__init__(
            code="IMAGE_UPLOAD_FAILED",
            message="이미지 업로드 중 오류가 발생했습니다.",
        )

class StorageServerUploadFailedException(BadGatewayException):
    def __init__(self) -> None:
        super().__init__(
            code="STORAGE_SERVER_UPLOAD_FAILED",
            message="이미지 업로드에 실패했습니다.",
        )

class StorageServerConnectionFailedException(ServiceUnavailableException):
    def __init__(self) -> None:
        super().__init__(
            code="STORAGE_SERVER_CONNECTION_FAILED",
            message="스토리지 서버를 사용할 수 없습니다.",
        )
