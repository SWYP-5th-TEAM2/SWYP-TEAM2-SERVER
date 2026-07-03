from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models import Image, Place, Plan, PlanStatus, User

ACTIVE_PLAN_STATUSES = {PlanStatus.VOTING, PlanStatus.CONFIRMED}


def find_active_place_by_id(
    db: Session,
    *,
    place_id: UUID,
) -> Place | None:
    stmt = select(Place).where(
        Place.id == place_id,
        Place.deleted_at.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def find_place_by_id_including_deleted(
    db: Session,
    *,
    place_id: UUID,
) -> Place | None:
    stmt = select(Place).where(Place.id == place_id)
    return db.execute(stmt).scalar_one_or_none()


def find_place_detail_row(
    db: Session,
    *,
    place_id: UUID,
) -> tuple[Place, str | None, str | None] | None:
    source_image = Image
    stmt = (
        select(
            Place,
            User.nickname,
            source_image.image_url,
        )
        .outerjoin(User, User.id == Place.user_id)
        .outerjoin(
            source_image,
            and_(
                source_image.id == Place.source_image_id,
                source_image.deleted_at.is_(None),
            ),
        )
        .where(
            Place.id == place_id,
            Place.deleted_at.is_(None),
        )
    )
    result = db.execute(stmt).one_or_none()
    if result is None:
        return None
    place, nickname, image_url = result
    return place, nickname, image_url


def find_place_list_rows(
    db: Session,
    *,
    room_id: UUID,
    keyword: str | None,
    offset: int,
    limit: int,
) -> list[tuple[Place, str | None]]:
    conditions = [
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    ]
    if keyword:
        like_keyword = f"%{keyword}%"
        conditions.append(
            or_(
                Place.title.ilike(like_keyword),
                Place.name.ilike(like_keyword),
                Place.location.ilike(like_keyword),
            )
        )

    stmt = (
        select(Place, User.nickname)
        .outerjoin(User, User.id == Place.user_id)
        .where(*conditions)
        .order_by(Place.created_at.desc(), Place.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.execute(stmt).all())


def count_active_places(
    db: Session,
    *,
    room_id: UUID,
    keyword: str | None = None,
) -> int:
    conditions = [
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
    ]
    if keyword:
        like_keyword = f"%{keyword}%"
        conditions.append(
            or_(
                Place.title.ilike(like_keyword),
                Place.name.ilike(like_keyword),
                Place.location.ilike(like_keyword),
            )
        )

    stmt = select(func.count(Place.id)).where(*conditions)
    return int(db.execute(stmt).scalar_one())


def create_place_row(
    db: Session,
    *,
    room_id: UUID,
    user_id: UUID,
    title: str,
    place_name: str | None,
    address: str | None,
    latitude: float | None,
    longitude: float | None,
    thumbnail_url: str | None,
    link_url: str | None,
    source_type: str | None,
    place_image_id: UUID | None,
    source_image_id: UUID | None,
) -> Place:
    place = Place(
        room_id=room_id,
        user_id=user_id,
        title=title,
        name=place_name,
        location=address,
        latitude=latitude,
        longitude=longitude,
        place_image=thumbnail_url,
        url=link_url,
        source=source_type,
        place_image_id=place_image_id,
        source_image_id=source_image_id,
    )
    db.add(place)
    db.flush()
    return place


def find_image_by_url(
    db: Session,
    *,
    image_url: str,
) -> Image | None:
    stmt = select(Image).where(
        Image.image_url == image_url,
        Image.deleted_at.is_(None),
    )
    return db.execute(stmt).scalar_one_or_none()


def exists_duplicate_place(
    db: Session,
    *,
    room_id: UUID,
    place_name: str | None,
    address: str | None,
    latitude: float | None,
    longitude: float | None,
    link_url: str | None,
    exclude_place_id: UUID | None = None,
) -> bool:
    duplicate_conditions = []

    if place_name and address:
        duplicate_conditions.append(
            and_(
                Place.name == place_name,
                Place.location == address,
            )
        )

    if latitude is not None and longitude is not None:
        duplicate_conditions.append(
            and_(
                Place.latitude == latitude,
                Place.longitude == longitude,
            )
        )

    if link_url:
        duplicate_conditions.append(Place.url == link_url)

    if not duplicate_conditions:
        return False

    conditions = [
        Place.room_id == room_id,
        Place.deleted_at.is_(None),
        or_(*duplicate_conditions),
    ]
    if exclude_place_id is not None:
        conditions.append(Place.id != exclude_place_id)

    stmt = select(Place.id).where(*conditions).limit(1)
    return db.execute(stmt).scalar_one_or_none() is not None


def place_has_active_plan(
    db: Session,
    *,
    place_id: UUID,
) -> bool:
    stmt = (
        select(Plan.id)
        .where(
            Plan.place_id == place_id,
            Plan.deleted_at.is_(None),
            Plan.status.in_(ACTIVE_PLAN_STATUSES),
        )
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none() is not None


def soft_delete_place(
    db: Session,
    *,
    place: Place,
    deleted_at: datetime,
) -> None:
    place.deleted_at = deleted_at
    db.flush()
