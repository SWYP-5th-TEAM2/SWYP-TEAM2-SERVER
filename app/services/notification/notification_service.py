from datetime import datetime, timedelta, timezone
from math import ceil
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    NotificationAccessDeniedException,
    NotificationDeletedException,
    NotificationIdInvalidException,
    NotificationListLookupFailedException,
    NotificationNotFoundException,
    NotificationNotPlanResponseException,
    NotificationPageValueInvalidException,
    NotificationPlanAlreadyClosedException,
    NotificationPlanNotFoundException,
    NotificationReadAllFailedException,
    NotificationReadFailedException,
    NotificationResponseAccessDeniedException,
    NotificationVoteScreenLookupFailedException,
    PlanDeletedException,
    RoomAccessDeniedException,
    RoomIdInvalidException,
    RoomNotFoundException,
    UserNotFoundException,
)
from app.models import Notification, NotificationTargetType, NotificationType, Plan, PlanStatus, Vote
from app.models.user.enums import UserAccountStatus
from app.repository.notification import (
    count_going_votes_for_plan,
    count_notifications_for_user,
    find_notification_by_id_including_deleted,
    find_notifications_for_user,
    find_place_by_id_for_notification,
    find_plan_by_id_for_notification,
    find_room_by_id_for_notification,
    find_user_preview_for_notification,
    find_vote_by_id_for_notification,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.repository.plan import find_members_by_ids, find_vote_by_plan_and_user, find_votes_by_plan_id
from app.repository.room import find_active_room_member
from app.repository.user import find_user_by_id
from app.schemas.notification import (
    NotificationInvitationPlaceResponse,
    NotificationListResponse,
    NotificationPageInfoResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
    NotificationUserBasicResponse,
    NotificationUserPreviewResponse,
    NotificationVoteScreenResponse,
)

KST = timezone(timedelta(hours=9))
DEFAULT_PAGE = 0
DEFAULT_SIZE = 20
MAX_PAGE_SIZE = 50

RESPONSE_GOING = "GOING"
RESPONSE_NOT_GOING = "NOT_GOING"
RESPONSE_PENDING = "PENDING"
RESPONSE_NOTIFICATION_TYPES = {
    NotificationType.PLAN_REQUESTED,
    NotificationType.RESPONSE_DEADLINE_SOON,
}


def _now() -> datetime:
    return datetime.now(KST)


def _parse_uuid(value: object, exception_factory) -> UUID:
    try:
        if value is None:
            raise ValueError
        return UUID(str(value))
    except (TypeError, ValueError):
        raise exception_factory()


def _parse_notification_id(notification_id: object) -> UUID:
    return _parse_uuid(notification_id, NotificationIdInvalidException)


def _parse_optional_room_id(room_id: object) -> UUID | None:
    if room_id is None or room_id == "":
        return None
    return _parse_uuid(room_id, RoomIdInvalidException)


def _ensure_room_filter_access(db: Session, *, user_id: UUID, room_id: UUID | None) -> None:
    if room_id is None:
        return
    room = find_room_by_id_for_notification(db=db, room_id=room_id)
    if room is None:
        raise RoomNotFoundException()
    if find_active_room_member(db=db, room_id=room_id, user_id=user_id) is None:
        raise RoomAccessDeniedException()


def _parse_page(value: object) -> int:
    if value is None or value == "":
        return DEFAULT_PAGE
    try:
        page = int(value)
    except (TypeError, ValueError):
        raise NotificationPageValueInvalidException()
    if page < 0:
        raise NotificationPageValueInvalidException()
    return page


def _parse_size(value: object) -> int:
    if value is None or value == "":
        return DEFAULT_SIZE
    try:
        size = int(value)
    except (TypeError, ValueError):
        raise NotificationPageValueInvalidException()
    if size < 1 or size > MAX_PAGE_SIZE:
        raise NotificationPageValueInvalidException()
    return size


def _ensure_active_user(db: Session, *, user_id: UUID) -> None:
    user = find_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise UserNotFoundException()
    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()


def _ensure_own_notification(
    db: Session,
    *,
    user_id: UUID,
    notification_id: UUID,
) -> Notification:
    notification = find_notification_by_id_including_deleted(db=db, notification_id=notification_id)
    if notification is None:
        raise NotificationNotFoundException()
    if notification.deleted_at is not None:
        raise NotificationDeletedException()
    if notification.user_id != user_id:
        raise NotificationAccessDeniedException()
    return notification


def _plan_status_for_notification(plan: Plan | None) -> str | None:
    if plan is None:
        return None
    # 외부 응답에서는 RECRUITING으로 변환하지 않고 DB enum 값인 VOTING을 그대로 사용한다.
    return plan.status.value


def _response_status_from_vote(vote: Vote | None) -> str:
    if vote is None:
        return RESPONSE_PENDING
    return RESPONSE_GOING if vote.is_attending else RESPONSE_NOT_GOING


def _actor_dict(*, user_id: UUID | None, nickname: str | None) -> dict[str, object | None] | None:
    if user_id is None and nickname is None:
        return None
    return {
        "userId": user_id,
        "nickname": nickname,
    }


def _plan_requested_item(db: Session, *, notification: Notification, plan: Plan) -> dict[str, object]:
    item: dict[str, object] = {
        "notificationId": notification.id,
        "type": notification.type.value,
        "isRead": notification.is_read,
        "createdAt": notification.created_at,
    }
    creator_row = find_user_preview_for_notification(db=db, user_id=plan.creator_id)
    if creator_row is not None:
        item["actor"] = _actor_dict(user_id=creator_row[0], nickname=creator_row[1])
    item["plan"] = {
        "planId": plan.id,
        "status": _plan_status_for_notification(plan),
        "responseDeadlineAt": plan.voting_ends_at,
    }
    if plan.place_id is not None:
        place = find_place_by_id_for_notification(db=db, place_id=plan.place_id)
        if place is not None:
            item["place"] = {
                "placeId": place.id,
                "title": place.title,
            }
    return item


def _plan_confirmed_item(db: Session, *, notification: Notification, plan: Plan) -> dict[str, object]:
    item: dict[str, object] = {
        "notificationId": notification.id,
        "type": notification.type.value,
        "isRead": notification.is_read,
        "createdAt": notification.created_at,
        "plan": {
            "planId": plan.id,
            "status": _plan_status_for_notification(plan),
            "confirmedAt": plan.confirmed_at,
            "scheduledAt": plan.start_time,
        },
    }
    if plan.place_id is not None:
        place = find_place_by_id_for_notification(db=db, place_id=plan.place_id)
        if place is not None:
            item["place"] = {
                "placeId": place.id,
                "placeName": place.name,
            }
    return item


def _member_going_item(db: Session, *, notification: Notification, vote: Vote) -> dict[str, object]:
    item: dict[str, object] = {
        "notificationId": notification.id,
        "type": notification.type.value,
        "isRead": notification.is_read,
        "createdAt": notification.created_at,
    }
    actor_row = find_user_preview_for_notification(db=db, user_id=vote.user_id)
    if actor_row is not None:
        item["actor"] = _actor_dict(user_id=actor_row[0], nickname=actor_row[1])
    plan = find_plan_by_id_for_notification(db=db, plan_id=vote.plan_id)
    if plan is not None and plan.deleted_at is None:
        item["plan"] = {
            "planId": plan.id,
            "status": _plan_status_for_notification(plan),
            "goingCount": count_going_votes_for_plan(db=db, plan_id=plan.id),
        }
    item["response"] = {
        "responseStatus": _response_status_from_vote(vote),
        "respondedAt": vote.updated_at or vote.created_at,
    }
    return item


def _quiet_recommendation_item(db: Session, *, notification: Notification) -> dict[str, object]:
    return {
        "notificationId": notification.id,
        "type": notification.type.value,
        "isRead": notification.is_read,
        "createdAt": notification.created_at,
    }


def _fallback_item(notification: Notification) -> dict[str, object]:
    return {
        "notificationId": notification.id,
        "type": notification.type.value,
        "isRead": notification.is_read,
        "createdAt": notification.created_at,
    }


def _build_notification_item(db: Session, *, notification: Notification) -> dict[str, object]:
    try:
        if notification.type in {NotificationType.PLAN_REQUESTED, NotificationType.RESPONSE_DEADLINE_SOON}:
            if notification.target_type != NotificationTargetType.PLAN or notification.target_id is None:
                return _fallback_item(notification)
            plan = find_plan_by_id_for_notification(db=db, plan_id=notification.target_id)
            if plan is None or plan.deleted_at is not None:
                return _fallback_item(notification)
            return _plan_requested_item(db=db, notification=notification, plan=plan)

        if notification.type == NotificationType.PLAN_CONFIRMED:
            if notification.target_type != NotificationTargetType.PLAN or notification.target_id is None:
                return _fallback_item(notification)
            plan = find_plan_by_id_for_notification(db=db, plan_id=notification.target_id)
            if plan is None or plan.deleted_at is not None:
                return _fallback_item(notification)
            return _plan_confirmed_item(db=db, notification=notification, plan=plan)

        if notification.type == NotificationType.MEMBER_GOING:
            if notification.target_type != NotificationTargetType.VOTE or notification.target_id is None:
                return _fallback_item(notification)
            vote = find_vote_by_id_for_notification(db=db, vote_id=notification.target_id)
            if vote is None:
                return _fallback_item(notification)
            return _member_going_item(db=db, notification=notification, vote=vote)

        if notification.type == NotificationType.QUIET_RECOMMENDATION:
            return _quiet_recommendation_item(db=db, notification=notification)

        return _fallback_item(notification)
    except SQLAlchemyError:
        raise
    except Exception:
        # 연결 대상 일부가 예외적인 상태여도 알림 목록 전체 조회는 막지 않는다.
        return _fallback_item(notification)


def get_notification_list(
    db: Session,
    *,
    user_id: UUID,
    page: object,
    size: object,
    room_id: object = None,
) -> NotificationListResponse:
    parsed_page = _parse_page(page)
    parsed_size = _parse_size(size)
    parsed_room_id = _parse_optional_room_id(room_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_filter_access(db=db, user_id=user_id, room_id=parsed_room_id)
        total_count = count_notifications_for_user(db=db, user_id=user_id, room_id=parsed_room_id)
        notifications = find_notifications_for_user(
            db=db,
            user_id=user_id,
            offset=parsed_page * parsed_size,
            limit=parsed_size,
            room_id=parsed_room_id,
        )
        total_pages = ceil(total_count / parsed_size) if total_count else 0
        return NotificationListResponse(
            server_time=_now(),
            notifications=[
                _build_notification_item(db=db, notification=notification)
                for notification in notifications
            ],
            page_info=NotificationPageInfoResponse(
                page=parsed_page,
                size=parsed_size,
                total_elements=total_count,
                total_pages=total_pages,
                has_next=parsed_page + 1 < total_pages,
            ),
        )
    except (
        NotificationPageValueInvalidException,
        RoomIdInvalidException,
        RoomNotFoundException,
        RoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise NotificationListLookupFailedException() from exc


def get_notification_vote_screen(
    db: Session,
    *,
    user_id: UUID,
    notification_id: object,
) -> NotificationVoteScreenResponse:
    parsed_notification_id = _parse_notification_id(notification_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        notification = _ensure_own_notification(
            db=db,
            user_id=user_id,
            notification_id=parsed_notification_id,
        )
        if notification.type not in RESPONSE_NOTIFICATION_TYPES:
            raise NotificationNotPlanResponseException()
        if notification.target_type != NotificationTargetType.PLAN or notification.target_id is None:
            raise NotificationNotPlanResponseException()

        plan = find_plan_by_id_for_notification(db=db, plan_id=notification.target_id)
        if plan is None:
            raise NotificationPlanNotFoundException()
        if plan.deleted_at is not None:
            raise PlanDeletedException()
        if plan.status != PlanStatus.VOTING:
            raise NotificationPlanAlreadyClosedException()
        if plan.room_id is None:
            raise NotificationResponseAccessDeniedException()
        if find_active_room_member(db=db, room_id=plan.room_id, user_id=user_id) is None:
            raise NotificationResponseAccessDeniedException()
        if plan.creator_id == user_id:
            raise NotificationResponseAccessDeniedException()

        place = find_place_by_id_for_notification(db=db, place_id=plan.place_id) if plan.place_id else None
        proposer_row = find_user_preview_for_notification(db=db, user_id=plan.creator_id)
        proposed_by = NotificationUserBasicResponse(
            user_id=proposer_row[0] if proposer_row else plan.creator_id,
            nickname=proposer_row[1] if proposer_row else None,
        )
        votes = find_votes_by_plan_id(db=db, plan_id=plan.id)
        my_vote = find_vote_by_plan_and_user(db=db, plan_id=plan.id, user_id=user_id)
        going_user_ids = [vote.user_id for vote in votes if vote.is_attending]
        going_members = [
            NotificationUserPreviewResponse(
                user_id=row[0],
                nickname=row[1],
                profile_image_url=row[2],
            )
            for row in find_members_by_ids(db=db, user_ids=going_user_ids)
        ]

        return NotificationVoteScreenResponse(
            notification_id=notification.id,
            plan_id=plan.id,
            room_id=plan.room_id,
            plan_status=_plan_status_for_notification(plan),
            proposed_by=proposed_by,
            place=NotificationInvitationPlaceResponse(
                place_id=place.id if place else None,
                title=place.title if place else None,
                place_name=place.name if place else None,
                thumbnail_url=place.place_image if place else None,
            ),
            scheduled_at=plan.start_time,
            response_deadline_at=plan.voting_ends_at,
            server_time=_now(),
            going_member_count=len(going_members),
            going_members=going_members,
            my_response_status=_response_status_from_vote(my_vote),
        )
    except (
        NotificationIdInvalidException,
        NotificationNotFoundException,
        NotificationDeletedException,
        NotificationAccessDeniedException,
        NotificationNotPlanResponseException,
        NotificationResponseAccessDeniedException,
        NotificationPlanAlreadyClosedException,
        NotificationPlanNotFoundException,
        PlanDeletedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise NotificationVoteScreenLookupFailedException() from exc


def read_notification(
    db: Session,
    *,
    user_id: UUID,
    notification_id: object,
) -> NotificationReadResponse:
    parsed_notification_id = _parse_notification_id(notification_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        notification = _ensure_own_notification(
            db=db,
            user_id=user_id,
            notification_id=parsed_notification_id,
        )
        notification = mark_notification_read(db=db, notification=notification)
        db.commit()
        return NotificationReadResponse(notification_id=notification.id, is_read=notification.is_read)
    except (
        NotificationIdInvalidException,
        NotificationNotFoundException,
        NotificationDeletedException,
        NotificationAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise NotificationReadFailedException() from exc


def read_all_notifications(db: Session, *, user_id: UUID) -> NotificationReadAllResponse:
    try:
        _ensure_active_user(db=db, user_id=user_id)
        read_count = mark_all_notifications_read(db=db, user_id=user_id)
        db.commit()
        return NotificationReadAllResponse(read_count=read_count)
    except (UserNotFoundException, ForbiddenException):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise NotificationReadAllFailedException() from exc
