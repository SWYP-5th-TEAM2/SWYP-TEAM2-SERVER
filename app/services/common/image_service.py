import uuid

from azure.core.exceptions import ServiceRequestError
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions.image import FileMissingException, UnsupportedImageFormatException, \
    UnsupportedImageSizeException
from app.core.storage.azure_blob import AzureBlobStorage
from app.models import ImagePurpose, Image
from app.schemas.image import ImageUploadResponse

ALLOWED_IMAGE_CONTENT_TYPES = [
    'image/jpeg',
    'image/png',
    "image/webp",
    "image/gif",
]

async def _validate_image_file(
    file: UploadFile | None,
) -> int:
    if file is None:
        raise FileMissingException()

    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise UnsupportedImageFormatException()

    contents = await file.read()
    file_size = len(contents)

    max_size = settings.max_image_size_mb * 1024 * 1024
    if file_size > max_size:
        raise UnsupportedImageSizeException()

    file.file.seek(0)

    return file_size

async def upload_image(
    db: Session,
    user_id: uuid.UUID,
    file: UploadFile,
    image_purpose: ImagePurpose,
) -> ImageUploadResponse:
    file_size = await _validate_image_file(file)
    storage = AzureBlobStorage()

    try:
        blob_name, image_url = await storage.upload_image(
            file=file,
            image_purpose=image_purpose.value,
            user_id=str(user_id),
        )
    except ServiceRequestError:
        raise


    image = Image(
        user_id=user_id,
        image_url=image_url,
        file_name=blob_name,
        file_size=file_size,
        content_type=str(file.content_type),
        image_purpose=image_purpose,
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return ImageUploadResponse(
        image_id=image.id,
        image_url=image.image_url,
    )

