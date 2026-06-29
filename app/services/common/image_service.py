import logging
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import (
    FileMissingException,
    ForbiddenException,
    ImagePurposeMissingException,
    ImageUploadFailedException,
    UnsupportedImageFormatException,
    UnsupportedImagePurposeException,
    UnsupportedImageSizeException,
    UserNotFoundException,
)
from app.core.storage.azure_blob import AzureBlobStorage
from app.models import Image, ImagePurpose
from app.models.user.enums import UserAccountStatus
from app.repository.user import find_user_by_id
from app.schemas.image import ImageUploadResponse

logger = logging.getLogger(__name__)

IMAGE_READ_CHUNK_SIZE = 1024 * 1024


def _detect_image_content_type(header: bytes) -> str | None:
    # 실제로 지원하는 이미지 형식인지 확인
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if (
        len(header) >= 12
        and header.startswith(b"RIFF")
        and header[8:12] == b"WEBP"
    ):
        return "image/webp"
    return None


def _parse_image_purpose(image_purpose: str | None) -> ImagePurpose:
    if image_purpose is None or not image_purpose.strip():
        raise ImagePurposeMissingException()

    try:
        return ImagePurpose(image_purpose.strip().upper())
    except ValueError:
        raise UnsupportedImagePurposeException()


async def _validate_image_file(
    file: UploadFile,
) -> tuple[int, str]:
    max_size = settings.max_image_size_mb * 1024 * 1024
    file_size = 0
    header = b""

    while chunk := await file.read(IMAGE_READ_CHUNK_SIZE):
        if len(header) < 16:
            header += chunk[: 16 - len(header)]

        file_size += len(chunk)
        if file_size > max_size:
            await file.seek(0)
            raise UnsupportedImageSizeException()

    # Azure 업로드가 파일 처음부터 읽을 수 있도록 포인터를 복원
    await file.seek(0)

    content_type = _detect_image_content_type(header)
    if content_type is None:
        raise UnsupportedImageFormatException()

    return file_size, content_type


async def upload_image(
    db: Session,
    user_id: UUID,
    file: UploadFile | None,
    image_purpose: str | None,
) -> ImageUploadResponse:
    parsed_image_purpose = _parse_image_purpose(image_purpose)
    if file is None:
        raise FileMissingException()

    try:
        user = find_user_by_id(
            db=db,
            user_id=user_id,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise ImageUploadFailedException() from exc

    if user is None:
        raise UserNotFoundException()
    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()

    db.rollback()

    file_size, content_type = await _validate_image_file(file)

    # Blob 업로드 성공 후 메타데이터 저장
    storage = AzureBlobStorage()
    blob_name, image_url = await storage.upload_image(
        file=file,
        image_purpose=parsed_image_purpose.value,
        user_id=str(user_id),
        content_type=content_type,
    )

    image = Image(
        user_id=user_id,
        image_url=image_url,
        file_name=blob_name,
        file_size=file_size,
        content_type=content_type,
        image_purpose=parsed_image_purpose,
    )

    try:
        db.add(image)
        db.flush()
        image_id = image.id
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()

        # DB 저장 실패 시 Blob을 삭제
        try:
            await storage.delete_image(blob_name)
        except Exception:
            logger.exception(
                "Failed to delete orphaned image blob: %s",
                blob_name,
            )

        raise ImageUploadFailedException() from exc

    return ImageUploadResponse(
        image_id=image_id,
        image_url=image_url,
    )
