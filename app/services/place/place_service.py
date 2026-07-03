import re
from datetime import datetime, timezone
from math import ceil
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    PlaceAddressTooLongException,
    PlaceAlreadyExistsException,
    PlaceCoordinateInvalidException,
    PlaceCreateFailedException,
    PlaceDeletedException,
    PlaceDeleteAccessDeniedException,
    PlaceDeleteFailedException,
    PlaceDetailLookupFailedException,
    PlaceIdInvalidException,
    PlaceImageUrlInvalidException,
    PlaceKeywordTooLongException,
    PlaceLinkUrlInvalidException,
    PlaceListLookupFailedException,
    PlaceModifyAccessDeniedException,
    PlaceNameTooLongException,
    PlaceNotFoundException,
    PlacePageValueInvalidException,
    PlaceRequestBodyMissingException,
    PlaceRoomAccessDeniedException,
    PlaceRoomIdInvalidException,
    PlaceRoomIdMissingException,
    PlaceRoomNotFoundException,
    PlaceTitleMissingException,
    PlaceTitleTooLongException,
    PlaceUpdateFailedException,
    PlaceUpdateFieldsMissingException,
    PlaceUsedInActivePlanException,
    UnsupportedPlaceLinkUrlException,
    UserNotFoundException,
)
from app.models import Place, User
from app.models.user.enums import UserAccountStatus
from app.repository.place import (
    count_active_places,
    create_place_row,
    exists_duplicate_place,
    find_image_by_url,
    find_place_by_id_including_deleted,
    find_place_detail_row,
    find_place_list_rows,
    place_has_active_plan,
    soft_delete_place,
)
from app.repository.room import find_active_room_member, find_room_by_id
from app.repository.user import find_user_by_id
from app.schemas.place import (
    CreatePlaceRequest,
    CreatePlaceResponse,
    DeletePlaceResponse,
    PlaceCreatorResponse,
    PlaceDetailResponse,
    PlaceListResponse,
    PlacePageInfoResponse,
    PlaceSummaryResponse,
    UpdatePlaceRequest,
    UpdatePlaceResponse,
)

MAX_TITLE_LENGTH = 30
MAX_PLACE_NAME_LENGTH = 30
MAX_ADDRESS_LENGTH = 255
MAX_KEYWORD_LENGTH = 30
MAX_PAGE_SIZE = 50
DEFAULT_PAGE = 0
DEFAULT_SIZE = 20
URL_MAX_LENGTH = 2048
SUPPORTED_URL_SCHEMES = {"http", "https"}


def _parse_uuid(value: object, exception_factory) -> UUID:
    try:
        if value is None:
            raise ValueError
        return UUID(str(value))
    except (TypeError, ValueError):
        raise exception_factory()


def _parse_room_id(room_id: object) -> UUID:
    if room_id is None or (isinstance(room_id, str) and not room_id.strip()):
        raise PlaceRoomIdMissingException()
    return _parse_uuid(room_id, PlaceRoomIdInvalidException)


def _parse_place_id(place_id: object) -> UUID:
    return _parse_uuid(place_id, PlaceIdInvalidException)


def _validate_title(value: object) -> str:
    if value is None or not isinstance(value, str) or not value.strip():
        raise PlaceTitleMissingException()
    title = value.strip()
    if len(title) > MAX_TITLE_LENGTH:
        raise PlaceTitleTooLongException()
    return title


def _normalize_optional_text(value: object, *, max_length: int, exception_factory) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > max_length:
        raise exception_factory()
    return normalized


def _normalize_place_name(value: object) -> str | None:
    return _normalize_optional_text(
        value,
        max_length=MAX_PLACE_NAME_LENGTH,
        exception_factory=PlaceNameTooLongException,
    )


def _normalize_address(value: object) -> str | None:
    return _normalize_optional_text(
        value,
        max_length=MAX_ADDRESS_LENGTH,
        exception_factory=PlaceAddressTooLongException,
    )


def _normalize_source_type(value: object) -> str | None:
    return _normalize_optional_text(
        value,
        max_length=100,
        exception_factory=PlaceAddressTooLongException,
    )


def _parse_optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise PlaceCoordinateInvalidException()


def _normalize_coordinates(
    latitude_value: object,
    longitude_value: object,
) -> tuple[float | None, float | None]:
    latitude = _parse_optional_float(latitude_value)
    longitude = _parse_optional_float(longitude_value)

    if latitude is None and longitude is None:
        return None, None
    if latitude is None or longitude is None:
        raise PlaceCoordinateInvalidException()
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise PlaceCoordinateInvalidException()
    return latitude, longitude


def _normalize_url(value: object, *, image: bool = False) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        if image:
            raise PlaceImageUrlInvalidException()
        raise PlaceLinkUrlInvalidException()

    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) > URL_MAX_LENGTH:
        if image:
            raise PlaceImageUrlInvalidException()
        raise PlaceLinkUrlInvalidException()

    parsed = urlparse(normalized)
    if parsed.scheme.lower() not in SUPPORTED_URL_SCHEMES or not parsed.netloc:
        if image:
            raise PlaceImageUrlInvalidException()
        raise PlaceLinkUrlInvalidException()

    if not image and parsed.scheme.lower() not in SUPPORTED_URL_SCHEMES:
        raise UnsupportedPlaceLinkUrlException()

    return normalized


def _parse_page(value: object) -> int:
    if value is None or value == "":
        return DEFAULT_PAGE
    try:
        page = int(value)
    except (TypeError, ValueError):
        raise PlacePageValueInvalidException()
    if page < 0:
        raise PlacePageValueInvalidException()
    return page


def _parse_size(value: object) -> int:
    if value is None or value == "":
        return DEFAULT_SIZE
    try:
        size = int(value)
    except (TypeError, ValueError):
        raise PlacePageValueInvalidException()
    if size < 1 or size > MAX_PAGE_SIZE:
        raise PlacePageValueInvalidException()
    return size


def _normalize_keyword(keyword: str | None) -> str | None:
    if keyword is None:
        return None
    normalized = keyword.strip()
    if not normalized:
        return None
    if len(normalized) > MAX_KEYWORD_LENGTH:
        raise PlaceKeywordTooLongException()
    return normalized


def _ensure_active_user(db: Session, *, user_id: UUID) -> User:
    user = find_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise UserNotFoundException()
    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()
    return user


def _ensure_room_member(db: Session, *, room_id: UUID, user_id: UUID) -> None:
    room = find_room_by_id(db=db, room_id=room_id)
    if room is None:
        raise PlaceRoomNotFoundException()

    room_member = find_active_room_member(
        db=db,
        room_id=room_id,
        user_id=user_id,
    )
    if room_member is None:
        raise PlaceRoomAccessDeniedException()


def _ensure_place_accessible(db: Session, *, place_id: UUID, user_id: UUID) -> Place:
    place = find_place_by_id_including_deleted(db=db, place_id=place_id)
    if place is None:
        raise PlaceNotFoundException()
    if place.deleted_at is not None:
        raise PlaceDeletedException()

    _ensure_room_member(db=db, room_id=place.room_id, user_id=user_id)
    return place


def _ensure_modify_permission(place: Place, *, user_id: UUID, delete: bool = False) -> None:
    # 현재는 등록자만 수정/삭제 가능하게 둔다.
    # 추후 방장 권한까지 허용할 경우 room_members.role 검사를 추가하면 된다.
    if place.user_id != user_id:
        if delete:
            raise PlaceDeleteAccessDeniedException()
        raise PlaceModifyAccessDeniedException()


def _build_creator(user_id: UUID | None, nickname: str | None) -> PlaceCreatorResponse:
    return PlaceCreatorResponse(
        user_id=user_id,
        nickname=nickname,
    )


def _find_image_id_by_url(db: Session, image_url: str | None) -> UUID | None:
    if image_url is None:
        return None
    image = find_image_by_url(db=db, image_url=image_url)
    if image is None:
        raise PlaceImageUrlInvalidException()
    return image.id


def _build_summary(place: Place, nickname: str | None) -> PlaceSummaryResponse:
    return PlaceSummaryResponse(
        place_id=place.id,
        title=place.title,
        place_name=place.name,
        address=place.location,
        thumbnail_url=place.place_image,
        created_by=_build_creator(place.user_id, nickname),
    )


def _build_detail(place: Place, nickname: str | None, image_url: str | None) -> PlaceDetailResponse:
    return PlaceDetailResponse(
        place_id=place.id,
        room_id=place.room_id,
        title=place.title,
        place_name=place.name,
        address=place.location,
        latitude=place.latitude,
        longitude=place.longitude,
        thumbnail_url=place.place_image,
        link_url=place.url,
        image_url=image_url,
        created_by=_build_creator(place.user_id, nickname),
    )


def get_places(
    db: Session,
    *,
    user_id: UUID,
    room_id: object,
    keyword: str | None,
    page: object,
    size: object,
) -> PlaceListResponse:
    parsed_room_id = _parse_room_id(room_id)
    normalized_keyword = _normalize_keyword(keyword)
    parsed_page = _parse_page(page)
    parsed_size = _parse_size(size)

    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=parsed_room_id, user_id=user_id)

        room = find_room_by_id(db=db, room_id=parsed_room_id)
        if room is None:
            raise PlaceRoomNotFoundException()

        total_count = count_active_places(
            db=db,
            room_id=parsed_room_id,
            keyword=normalized_keyword,
        )
        rows = find_place_list_rows(
            db=db,
            room_id=parsed_room_id,
            keyword=normalized_keyword,
            offset=parsed_page * parsed_size,
            limit=parsed_size,
        )
        total_pages = ceil(total_count / parsed_size) if total_count else 0

        return PlaceListResponse(
            room_id=room.id,
            room_name=room.name,
            place_count=total_count,
            places=[_build_summary(place, nickname) for place, nickname in rows],
            page_info=PlacePageInfoResponse(
                page=parsed_page,
                size=parsed_size,
                total_elements=total_count,
                total_pages=total_pages,
                has_next=parsed_page + 1 < total_pages,
            ),
        )
    except (PlaceRoomNotFoundException, PlaceRoomAccessDeniedException, UserNotFoundException, ForbiddenException):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceListLookupFailedException() from exc


def get_place_detail(
    db: Session,
    *,
    user_id: UUID,
    place_id: object,
) -> PlaceDetailResponse:
    parsed_place_id = _parse_place_id(place_id)

    try:
        _ensure_active_user(db=db, user_id=user_id)
        place = _ensure_place_accessible(db=db, place_id=parsed_place_id, user_id=user_id)
        row = find_place_detail_row(db=db, place_id=place.id)
        if row is None:
            raise PlaceNotFoundException()
        place, nickname, image_url = row
        return _build_detail(place, nickname, image_url)
    except (PlaceNotFoundException, PlaceDeletedException, PlaceRoomAccessDeniedException, PlaceRoomNotFoundException, UserNotFoundException, ForbiddenException):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceDetailLookupFailedException() from exc


def create_place(
    db: Session,
    *,
    user_id: UUID,
    request: CreatePlaceRequest | None,
) -> CreatePlaceResponse:
    if request is None:
        raise PlaceRequestBodyMissingException()

    room_id = _parse_room_id(request.room_id)
    title = _validate_title(request.title)
    place_name = _normalize_place_name(request.place_name)
    address = _normalize_address(request.address)
    latitude, longitude = _normalize_coordinates(request.latitude, request.longitude)
    thumbnail_url = _normalize_url(request.thumbnail_url, image=True)
    link_url = _normalize_url(request.link_url)
    image_url = _normalize_url(request.image_url, image=True)
    source_type = _normalize_source_type(request.source_type)

    try:
        user = _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=room_id, user_id=user_id)

        if exists_duplicate_place(
            db=db,
            room_id=room_id,
            place_name=place_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            link_url=link_url,
        ):
            raise PlaceAlreadyExistsException()

        place_image_id = None
        if thumbnail_url:
            image = find_image_by_url(db=db, image_url=thumbnail_url)
            place_image_id = image.id if image else None
        source_image_id = _find_image_id_by_url(db=db, image_url=image_url)

        place = create_place_row(
            db=db,
            room_id=room_id,
            user_id=user_id,
            title=title,
            place_name=place_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            thumbnail_url=thumbnail_url,
            link_url=link_url,
            source_type=source_type,
            place_image_id=place_image_id,
            source_image_id=source_image_id,
        )
        place_id = place.id
        db.commit()

        return CreatePlaceResponse(
            place_id=place_id,
            room_id=room_id,
            title=place.title,
            place_name=place.name,
            address=place.location,
            thumbnail_url=place.place_image,
            created_by=_build_creator(user.id, user.nickname),
        )
    except (PlaceAlreadyExistsException, PlaceRoomNotFoundException, PlaceRoomAccessDeniedException, PlaceImageUrlInvalidException, UserNotFoundException, ForbiddenException):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceCreateFailedException() from exc


def update_place(
    db: Session,
    *,
    user_id: UUID,
    place_id: object,
    request: UpdatePlaceRequest | None,
) -> UpdatePlaceResponse:
    if request is None:
        raise PlaceRequestBodyMissingException()

    parsed_place_id = _parse_place_id(place_id)
    provided_fields = request.model_dump(exclude_unset=True)
    if not provided_fields:
        raise PlaceUpdateFieldsMissingException()

    try:
        user = _ensure_active_user(db=db, user_id=user_id)
        place = _ensure_place_accessible(db=db, place_id=parsed_place_id, user_id=user_id)
        _ensure_modify_permission(place, user_id=user_id)

        if place_has_active_plan(db=db, place_id=place.id):
            raise PlaceUsedInActivePlanException()

        title = place.title
        place_name = place.name
        address = place.location
        latitude = place.latitude
        longitude = place.longitude
        thumbnail_url = place.place_image
        link_url = place.url
        source_type = place.source
        source_image_id = place.source_image_id
        place_image_id = place.place_image_id

        if "title" in provided_fields:
            title = _validate_title(request.title)
        if "place_name" in provided_fields:
            place_name = _normalize_place_name(request.place_name)
        if "address" in provided_fields:
            address = _normalize_address(request.address)
        if "latitude" in provided_fields or "longitude" in provided_fields:
            latitude, longitude = _normalize_coordinates(
                request.latitude if "latitude" in provided_fields else latitude,
                request.longitude if "longitude" in provided_fields else longitude,
            )
        if "thumbnail_url" in provided_fields:
            thumbnail_url = _normalize_url(request.thumbnail_url, image=True)
            place_image = find_image_by_url(db=db, image_url=thumbnail_url) if thumbnail_url else None
            place_image_id = place_image.id if place_image else None
        if "link_url" in provided_fields:
            link_url = _normalize_url(request.link_url)
        if "image_url" in provided_fields:
            image_url = _normalize_url(request.image_url, image=True)
            source_image_id = _find_image_id_by_url(db=db, image_url=image_url)
        if "source_type" in provided_fields:
            source_type = _normalize_source_type(request.source_type)

        if exists_duplicate_place(
            db=db,
            room_id=place.room_id,
            place_name=place_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            link_url=link_url,
            exclude_place_id=place.id,
        ):
            raise PlaceAlreadyExistsException()

        place.title = title
        place.name = place_name
        place.location = address
        place.latitude = latitude
        place.longitude = longitude
        place.place_image = thumbnail_url
        place.url = link_url
        place.source = source_type
        place.place_image_id = place_image_id
        place.source_image_id = source_image_id
        db.flush()
        db.commit()

        row = find_place_detail_row(db=db, place_id=place.id)
        image_url = row[2] if row else None
        return UpdatePlaceResponse(
            place_id=place.id,
            room_id=place.room_id,
            title=place.title,
            place_name=place.name,
            address=place.location,
            latitude=place.latitude,
            longitude=place.longitude,
            thumbnail_url=place.place_image,
            link_url=place.url,
            image_url=image_url,
            updated_by=_build_creator(user.id, user.nickname),
        )
    except (
        PlaceAlreadyExistsException,
        PlaceDeletedException,
        PlaceImageUrlInvalidException,
        PlaceModifyAccessDeniedException,
        PlaceNotFoundException,
        PlaceRoomAccessDeniedException,
        PlaceRoomNotFoundException,
        PlaceUsedInActivePlanException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceUpdateFailedException() from exc


def delete_place(
    db: Session,
    *,
    user_id: UUID,
    place_id: object,
) -> DeletePlaceResponse:
    parsed_place_id = _parse_place_id(place_id)

    try:
        _ensure_active_user(db=db, user_id=user_id)
        place = _ensure_place_accessible(db=db, place_id=parsed_place_id, user_id=user_id)
        _ensure_modify_permission(place, user_id=user_id, delete=True)

        if place_has_active_plan(db=db, place_id=place.id):
            raise PlaceUsedInActivePlanException()

        soft_delete_place(
            db=db,
            place=place,
            deleted_at=datetime.now(timezone.utc),
        )
        remaining_count = count_active_places(db=db, room_id=place.room_id)
        db.commit()

        return DeletePlaceResponse(
            place_id=place.id,
            remaining_place_count=remaining_count,
        )
    except (
        PlaceDeleteAccessDeniedException,
        PlaceDeletedException,
        PlaceNotFoundException,
        PlaceRoomAccessDeniedException,
        PlaceRoomNotFoundException,
        PlaceUsedInActivePlanException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceDeleteFailedException() from exc
