from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    PlaceImageExtractionFailedException,
    PlaceImageExtractionResponseInvalidException,
    PlaceImageExtractionServiceUnavailableException,
    PlaceImageFileMissingException,
    PlaceImageFileSizeExceededException,
    PlaceRoomAccessDeniedException,
    PlaceRoomNotFoundException,
    UnsupportedImageSizeException,
    UserNotFoundException,
)
from app.models import ImagePurpose
from app.schemas.image import ImageUploadResponse
from app.schemas.place import PlaceImageExtractionResponse
from app.services.common.image_service import _validate_image_file, upload_image
from app.services.place.ai_image_extraction_client import extract_places_from_image_with_ai
from app.services.place.place_service import _ensure_active_user, _ensure_room_member, _parse_room_id


async def extract_place_info_from_image(
    db: Session,
    *,
    user_id: UUID,
    room_id: object,
    file: UploadFile | None,
) -> PlaceImageExtractionResponse:
    parsed_room_id = _parse_room_id(room_id)
    if file is None:
        raise PlaceImageFileMissingException()

    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=parsed_room_id, user_id=user_id)
    except (
        PlaceRoomNotFoundException,
        PlaceRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceImageExtractionFailedException() from exc

    try:
        _, content_type = await _validate_image_file(file)
    except UnsupportedImageSizeException as exc:
        raise PlaceImageFileSizeExceededException() from exc

    try:
        image_bytes = await file.read()
        await file.seek(0)

        extracted_places = await extract_places_from_image_with_ai(
            image_bytes=image_bytes,
            content_type=content_type,
        )

        uploaded_image: ImageUploadResponse = await upload_image(
            db=db,
            user_id=user_id,
            file=file,
            image_purpose=ImagePurpose.SOURCE.value,
        )
        image_url = str(uploaded_image.image_url)

        return PlaceImageExtractionResponse(
            extraction_id=uuid.uuid4(),
            room_id=parsed_room_id,
            image_url=image_url,
            extracted_places=extracted_places,
        )
    except (
        PlaceImageExtractionResponseInvalidException,
        PlaceImageExtractionServiceUnavailableException,
        PlaceImageFileSizeExceededException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceImageExtractionFailedException() from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise PlaceImageExtractionFailedException() from exc
