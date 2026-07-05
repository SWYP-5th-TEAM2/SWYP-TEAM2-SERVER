from datetime import datetime, time, timedelta, timezone
from math import ceil
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    PlanAlreadyClosedException,
    PlanAlreadyExistsException,
    PlanCloseAccessDeniedException,
    PlanCloseFailedException,
    PlanCreateFailedException,
    PlanDeletedException,
    PlanDrawFailedException,
    PlanIdInvalidException,
    PlanInvitationLookupFailedException,
    PlanListLookupFailedException,
    PlanNoAttendingMemberException,
    PlanNoDrawablePlaceException,
    PlanNotFoundException,
    PlanPageValueInvalidException,
    PlanPendingMemberNotFoundException,
    PlanPlaceIdInvalidException,
    PlanPlaceNotFoundException,
    PlanPlaceNotInRoomException,
    PlanRequestBodyMissingException,
    PlanResponseAccessDeniedException,
    PlanResponseDeadlineAfterScheduleException,
    PlanResponseDeadlineInvalidException,
    PlanResponseDeadlineMissingException,
    PlanResponseDeadlinePassedException,
    PlanResponseDeadlinePastException,
    PlanResponseSaveFailedException,
    PlanResponseStatusMissingException,
    PlanResponsesLookupFailedException,
    PlanReminderFailedException,
    PlanRoomAccessDeniedException,
    PlanRoomIdInvalidException,
    PlanRoomIdMissingException,
    PlanRoomNotFoundException,
    PlanScheduledAtInvalidException,
    PlanScheduledAtMissingException,
    PlanScheduledAtPastException,
    PlanStatusFilterInvalidException,
    PlanTargetMemberMissingException,
    PlanTicketLookupFailedException,
    PlanTicketNotConfirmedException,
    UnsupportedPlanResponseStatusException,
    UserNotFoundException,
)
from app.models import DayOfWeek, NotificationTargetType, NotificationType, Place, Plan, PlanStatus, RoomMemberRole, User
from app.models.user.enums import UserAccountStatus
from app.repository.plan import (
    count_drawable_places,
    count_plans_by_status,
    count_target_members,
    create_notifications,
    create_plan_row,
    find_active_plan_for_place,
    find_members_by_ids,
    find_place_in_room,
    find_plan_by_id_including_deleted,
    find_plan_list_rows,
    find_plan_place_room_row,
    find_random_drawable_place,
    find_room_member_response_rows,
    find_target_member_previews,
    find_vote_by_plan_and_user,
    find_votes_by_plan_id,
    upsert_vote,
)
from app.repository.room import find_active_room_member, find_room_by_id
from app.repository.schedule import find_active_recurring_schedule_rows_by_user_ids
from app.repository.user import find_user_by_id
from app.services.notification import FcmDispatchResult, FcmPushPayload, dispatch_fcm_push_notifications
from app.schemas.plan import (
    ClosePlanResponse,
    CreatePlanRequest,
    CreatePlanResponse,
    DrawPlaceRequest,
    DrawPlaceResponse,
    DrawSummaryResponse,
    InvitationResponse,
    PickedPlaceCreatorResponse,
    PickedPlaceResponse,
    PlanListItemResponse,
    PlanListResponse,
    PlanListSummaryResponse,
    PlanMemberResponse,
    PlanInvitationPlaceResponse,
    PlanPageInfoResponse,
    PlanPlaceSummaryResponse,
    PlanResponseSummaryResponse,
    PlanUserBasicResponse,
    PlanResponsesPlanResponse,
    PlanResponsesResponse,
    PlanUserPreviewResponse,
    PushNotificationSummaryResponse,
    ReminderResponse,
    SavePlanResponseRequest,
    SavePlanResponseResponse,
    SavedPlanInfoResponse,
    TicketLookupResponse,
    TicketResponse,
)

KST = timezone(timedelta(hours=9))
DEFAULT_PAGE = 0
DEFAULT_SIZE = 20
MAX_PAGE_SIZE = 50
RESPONSE_DEADLINE_AFTER_DRAW_HOURS = 24
RECOMMEND_TIME_SLOT_MINUTES = 10
RECOMMEND_BUSINESS_START = time(hour=11)
RECOMMEND_BUSINESS_END = time(hour=20)
RECOMMEND_SEARCH_DAYS = 30
MAX_DRAW_EXCLUDED_PLACE_IDS = 200

RESPONSE_GOING = "GOING"
RESPONSE_NOT_GOING = "NOT_GOING"
RESPONSE_PENDING = "PENDING"

PLAN_STATUS_ALL = "ALL"
LEGACY_PLAN_STATUS_RECRUITING = "RECRUITING"  # 기존 앱 요청 호환용 입력 alias. 응답값으로는 사용하지 않는다.
PLAN_LIST_VISIBLE_STATUSES = (PlanStatus.VOTING, PlanStatus.CONFIRMED, PlanStatus.COMPLETED)
PLAN_RESPONSE_OPEN_STATUS = PlanStatus.VOTING

ENTRY_VIEW_STATUS = "STATUS"
ENTRY_VIEW_RESPONSE = "RESPONSE"
ENTRY_VIEW_CHANGE_RESPONSE = "CHANGE_RESPONSE"
ENTRY_VIEW_TICKET = "TICKET"


PYTHON_WEEKDAY_TO_DAY_OF_WEEK = {
    0: DayOfWeek.MON,
    1: DayOfWeek.TUE,
    2: DayOfWeek.WED,
    3: DayOfWeek.THU,
    4: DayOfWeek.FRI,
    5: DayOfWeek.SAT,
    6: DayOfWeek.SUN,
}


def _next_slot_after(value: datetime, *, minutes: int = RECOMMEND_TIME_SLOT_MINUTES) -> datetime:
    normalized = value.astimezone(KST)
    slot_seconds = minutes * 60
    seconds_since_midnight = (
        normalized.hour * 3600
        + normalized.minute * 60
        + normalized.second
    )
    remainder = seconds_since_midnight % slot_seconds
    if remainder == 0 and normalized.microsecond == 0:
        delta_seconds = slot_seconds
    else:
        delta_seconds = slot_seconds - remainder
    return (normalized + timedelta(seconds=delta_seconds)).replace(second=0, microsecond=0)


def _business_start_for_day(value: datetime) -> datetime:
    current = value.astimezone(KST)
    return datetime.combine(current.date(), RECOMMEND_BUSINESS_START, tzinfo=KST)


def _business_end_for_day(value: datetime) -> datetime:
    current = value.astimezone(KST)
    return datetime.combine(current.date(), RECOMMEND_BUSINESS_END, tzinfo=KST)


def _adjust_to_business_window(value: datetime) -> datetime:
    candidate = value.astimezone(KST)
    day_start = _business_start_for_day(candidate)
    day_end = _business_end_for_day(candidate)
    if candidate < day_start:
        return day_start
    if candidate >= day_end:
        return _business_start_for_day(candidate + timedelta(days=1))
    return candidate


def _has_recurring_schedule_conflict(
    *,
    candidate: datetime,
    user_id: UUID,
    recurring_schedule_map: dict[UUID, dict[DayOfWeek, list[tuple[time, time]]]],
) -> bool:
    schedules_by_day = recurring_schedule_map.get(user_id)
    if not schedules_by_day:
        return False
    day_of_week = PYTHON_WEEKDAY_TO_DAY_OF_WEEK[candidate.weekday()]
    candidate_time = candidate.timetz().replace(tzinfo=None)
    for start_time, end_time in schedules_by_day.get(day_of_week, []):
        if start_time <= candidate_time < end_time:
            return True
    return False


def _build_recurring_schedule_map(
    rows: list[tuple[UUID, DayOfWeek, time, time]],
) -> dict[UUID, dict[DayOfWeek, list[tuple[time, time]]]]:
    schedule_map: dict[UUID, dict[DayOfWeek, list[tuple[time, time]]]] = {}
    for user_id, day_of_week, start_time, end_time in rows:
        schedule_map.setdefault(user_id, {}).setdefault(day_of_week, []).append((start_time, end_time))
    return schedule_map


def _find_recommended_scheduled_at(
    *,
    response_deadline_at: datetime,
    creator_id: UUID,
    room_member_ids: list[UUID],
    recurring_schedule_map: dict[UUID, dict[DayOfWeek, list[tuple[time, time]]]],
) -> datetime:
    first_candidate = _adjust_to_business_window(_next_slot_after(response_deadline_at))
    fallback_creator_available: datetime | None = None
    fallback_business_slot = first_candidate
    candidate = first_candidate
    checked_slots = 0
    max_slots = int((RECOMMEND_SEARCH_DAYS + 1) * 24 * 60 / RECOMMEND_TIME_SLOT_MINUTES)

    while checked_slots < max_slots:
        candidate = _adjust_to_business_window(candidate)
        if candidate >= _business_end_for_day(candidate):
            candidate = _business_start_for_day(candidate + timedelta(days=1))
            continue

        creator_available = not _has_recurring_schedule_conflict(
            candidate=candidate,
            user_id=creator_id,
            recurring_schedule_map=recurring_schedule_map,
        )
        if creator_available:
            if fallback_creator_available is None:
                fallback_creator_available = candidate
            group_available = all(
                not _has_recurring_schedule_conflict(
                    candidate=candidate,
                    user_id=member_id,
                    recurring_schedule_map=recurring_schedule_map,
                )
                for member_id in room_member_ids
            )
            if group_available:
                return candidate

        candidate = candidate + timedelta(minutes=RECOMMEND_TIME_SLOT_MINUTES)
        checked_slots += 1

    return fallback_creator_available or fallback_business_slot


def _now() -> datetime:
    return datetime.now(KST)


def _parse_uuid(value: object, exception_factory) -> UUID:
    try:
        if value is None:
            raise ValueError
        return UUID(str(value))
    except (TypeError, ValueError):
        raise exception_factory()


def _parse_room_id(room_id: object) -> UUID:
    if room_id is None or (isinstance(room_id, str) and not room_id.strip()):
        raise PlanRoomIdMissingException()
    return _parse_uuid(room_id, PlanRoomIdInvalidException)


def _parse_place_id(place_id: object) -> UUID:
    return _parse_uuid(place_id, PlanPlaceIdInvalidException)


def _parse_plan_id(plan_id: object) -> UUID:
    return _parse_uuid(plan_id, PlanIdInvalidException)


def _parse_datetime(value: object, *, missing_exception, invalid_exception) -> datetime:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise missing_exception()
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            raise invalid_exception()
    else:
        raise invalid_exception()

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _parse_page(value: object) -> int:
    if value is None or value == "":
        return DEFAULT_PAGE
    try:
        page = int(value)
    except (TypeError, ValueError):
        raise PlanPageValueInvalidException()
    if page < 0:
        raise PlanPageValueInvalidException()
    return page


def _parse_size(value: object) -> int:
    if value is None or value == "":
        return DEFAULT_SIZE
    try:
        size = int(value)
    except (TypeError, ValueError):
        raise PlanPageValueInvalidException()
    if size < 1 or size > MAX_PAGE_SIZE:
        raise PlanPageValueInvalidException()
    return size


def _parse_status_filter(value: str | None) -> tuple[str, list[PlanStatus] | None]:
    if value is None or not value.strip():
        return PLAN_STATUS_ALL, None
    normalized = value.strip().upper()
    if normalized == PLAN_STATUS_ALL:
        return PLAN_STATUS_ALL, None
    if normalized in {LEGACY_PLAN_STATUS_RECRUITING, PlanStatus.VOTING.value}:
        return PlanStatus.VOTING.value, [PlanStatus.VOTING]
    if normalized == PlanStatus.CONFIRMED.value:
        return PlanStatus.CONFIRMED.value, [PlanStatus.CONFIRMED]
    if normalized == PlanStatus.COMPLETED.value:
        return PlanStatus.COMPLETED.value, [PlanStatus.COMPLETED]
    raise PlanStatusFilterInvalidException()


def _parse_draw_excluded_place_ids(request: DrawPlaceRequest) -> list[UUID]:
    excluded_place_ids: list[UUID] = []
    seen_place_ids: set[UUID] = set()

    def append_place_id(value: object) -> None:
        if value in (None, ""):
            return
        parsed_place_id = _parse_place_id(value)
        if parsed_place_id not in seen_place_ids:
            excluded_place_ids.append(parsed_place_id)
            seen_place_ids.add(parsed_place_id)

    raw_excluded_place_ids = request.excluded_place_ids
    if raw_excluded_place_ids in (None, ""):
        return excluded_place_ids
    if not isinstance(raw_excluded_place_ids, list):
        raise PlanPlaceIdInvalidException()
    if len(raw_excluded_place_ids) > MAX_DRAW_EXCLUDED_PLACE_IDS:
        raise PlanPlaceIdInvalidException()

    for place_id in raw_excluded_place_ids:
        append_place_id(place_id)
    return excluded_place_ids


def _append_unique_place_id(place_ids: list[UUID], place_id: UUID) -> list[UUID]:
    if place_id in set(place_ids):
        return place_ids
    return [*place_ids, place_id]


def _parse_response_status(value: object) -> bool:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise PlanResponseStatusMissingException()
    normalized = str(value).strip().upper()
    if normalized == RESPONSE_GOING:
        return True
    if normalized == RESPONSE_NOT_GOING:
        return False
    raise UnsupportedPlanResponseStatusException()


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
        raise PlanRoomNotFoundException()
    room_member = find_active_room_member(db=db, room_id=room_id, user_id=user_id)
    if room_member is None:
        raise PlanRoomAccessDeniedException()


def _ensure_plan_accessible(db: Session, *, plan_id: UUID, user_id: UUID) -> Plan:
    plan = find_plan_by_id_including_deleted(db=db, plan_id=plan_id)
    if plan is None:
        raise PlanNotFoundException()
    if plan.deleted_at is not None:
        raise PlanDeletedException()
    if plan.room_id is None:
        raise PlanRoomAccessDeniedException()
    _ensure_room_member(db=db, room_id=plan.room_id, user_id=user_id)
    return plan


def _is_host_or_creator(db: Session, *, plan: Plan, user_id: UUID) -> bool:
    if plan.creator_id == user_id:
        return True
    if plan.room_id is None:
        return False
    member = find_active_room_member(db=db, room_id=plan.room_id, user_id=user_id)
    return bool(member and member.role == RoomMemberRole.HOST)


def _response_status_from_vote(is_attending: bool | None) -> str:
    if is_attending is None:
        return RESPONSE_PENDING
    return RESPONSE_GOING if is_attending else RESPONSE_NOT_GOING


def _plan_status_value(plan: Plan) -> str:
    # API 응답에는 DB enum 값을 그대로 사용한다.
    # 예전 문서/앱의 RECRUITING은 요청 alias로만 허용하고, 응답값은 VOTING으로 통일한다.
    return plan.status.value


def _build_user_preview(
    user_id: UUID | None,
    nickname: str | None,
    profile_image_url: str | None = None,
) -> PlanUserPreviewResponse:
    return PlanUserPreviewResponse(
        user_id=user_id,
        nickname=nickname,
        profile_image_url=profile_image_url,
    )


def _build_user_basic(
    user_id: UUID | None,
    nickname: str | None,
) -> PlanUserBasicResponse:
    return PlanUserBasicResponse(
        user_id=user_id,
        nickname=nickname,
    )


def _build_place_summary(place: Place | None) -> PlanPlaceSummaryResponse:
    return PlanPlaceSummaryResponse(
        place_id=place.id if place else None,
        title=place.title if place else None,
        place_name=place.name if place else None,
        address=place.location if place else None,
        thumbnail_url=place.place_image if place else None,
    )


def _build_invitation_place(place: Place | None) -> PlanInvitationPlaceResponse:
    return PlanInvitationPlaceResponse(
        place_id=place.id if place else None,
        title=place.title if place else None,
        place_name=place.name if place else None,
        thumbnail_url=place.place_image if place else None,
    )


def _build_plan_info(plan: Plan) -> PlanResponsesPlanResponse:
    return PlanResponsesPlanResponse(
        plan_id=plan.id,
        status=_plan_status_value(plan),
        scheduled_at=plan.start_time,
        response_deadline_at=plan.voting_ends_at,
    )


def _to_push_summary(result: FcmDispatchResult) -> PushNotificationSummaryResponse:
    return PushNotificationSummaryResponse(
        requested_count=result.target_user_count,
        sent_count=result.sent_count,
        failed_count=result.failed_count,
        push_status=result.push_status,
    )


def _build_push_payloads(
    *,
    notifications: list[Any],
    title: str,
    body: str,
) -> list[FcmPushPayload]:
    return [
        FcmPushPayload(
            user_id=notification.user_id,
            notification_id=notification.id,
            notification_type=notification.type,
            target_type=notification.target_type.value if notification.target_type else None,
            target_id=notification.target_id,
            title=title,
            body=body,
        )
        for notification in notifications
    ]


def _empty_push_summary(*, requested_count: int = 0) -> PushNotificationSummaryResponse:
    return PushNotificationSummaryResponse(
        requested_count=requested_count,
        sent_count=0,
        failed_count=0,
        push_status="SKIPPED",
    )


def _get_plan_context(db: Session, *, plan_id: UUID) -> tuple[Plan, Place | None, Any, str | None, str | None]:
    row = find_plan_place_room_row(db=db, plan_id=plan_id)
    if row is None:
        raise PlanNotFoundException()
    plan, place, room, creator_nickname, creator_profile_image_url = row
    if plan.deleted_at is not None:
        raise PlanDeletedException()
    return plan, place, room, creator_nickname, creator_profile_image_url


def _build_response_summary(
    *,
    target_member_count: int,
    votes: list[Any],
) -> PlanResponseSummaryResponse:
    going_count = sum(1 for vote in votes if vote.is_attending)
    not_going_count = sum(1 for vote in votes if not vote.is_attending)
    pending_count = max(target_member_count - going_count - not_going_count, 0)
    return PlanResponseSummaryResponse(
        going_count=going_count,
        not_going_count=not_going_count,
        pending_count=pending_count,
        total_target_count=target_member_count,
        responded_count=going_count + not_going_count,
    )


def _get_target_member_count(db: Session, *, plan: Plan) -> int:
    if plan.room_id is None or plan.creator_id is None:
        return 0
    return count_target_members(
        db=db,
        room_id=plan.room_id,
        excluded_user_id=plan.creator_id,
    )


def get_draw_summary(db: Session, *, user_id: UUID, room_id: object) -> DrawSummaryResponse:
    parsed_room_id = _parse_room_id(room_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=parsed_room_id, user_id=user_id)
        place_count = count_drawable_places(db=db, room_id=parsed_room_id)
        return DrawSummaryResponse(room_id=parsed_room_id, place_count=place_count)
    except (PlanRoomNotFoundException, PlanRoomAccessDeniedException, UserNotFoundException, ForbiddenException):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanDrawFailedException() from exc


def draw_place(db: Session, *, user_id: UUID, request: DrawPlaceRequest | None) -> DrawPlaceResponse:
    if request is None:
        raise PlanRequestBodyMissingException()
    room_id = _parse_room_id(request.room_id)
    excluded_place_ids = _parse_draw_excluded_place_ids(request)

    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=room_id, user_id=user_id)

        if count_drawable_places(db=db, room_id=room_id, exclude_place_ids=excluded_place_ids) == 0:
            raise PlanNoDrawablePlaceException()

        row = find_random_drawable_place(
            db=db,
            room_id=room_id,
            exclude_place_ids=excluded_place_ids,
        )
        if row is None:
            raise PlanNoDrawablePlaceException()

        place, nickname = row
        drawn_at = _now()
        recommended_response_deadline_at = drawn_at + timedelta(hours=RESPONSE_DEADLINE_AFTER_DRAW_HOURS)
        member_rows = find_room_member_response_rows(
            db=db,
            room_id=room_id,
            excluded_user_id=None,
        )
        room_member_ids = [member_id for member_id, _, _, _ in member_rows]
        recurring_schedule_rows = find_active_recurring_schedule_rows_by_user_ids(
            db=db,
            user_ids=room_member_ids,
        )
        recommended_scheduled_at = _find_recommended_scheduled_at(
            response_deadline_at=recommended_response_deadline_at,
            creator_id=user_id,
            room_member_ids=room_member_ids,
            recurring_schedule_map=_build_recurring_schedule_map(recurring_schedule_rows),
        )
        target_count = count_target_members(
            db=db,
            room_id=room_id,
            excluded_user_id=user_id,
        )
        next_excluded_place_ids = _append_unique_place_id(excluded_place_ids, place.id)
        remaining_drawable_place_count = count_drawable_places(
            db=db,
            room_id=room_id,
            exclude_place_ids=next_excluded_place_ids,
        )

        return DrawPlaceResponse(
            picked_place=PickedPlaceResponse(
                place_id=place.id,
                title=place.title,
                place_name=place.name,
                thumbnail_url=place.place_image,
                created_by=PickedPlaceCreatorResponse(
                    user_id=place.user_id,
                    nickname=nickname,
                ),
            ),
            recommended_scheduled_at=recommended_scheduled_at,
            recommended_response_deadline_at=recommended_response_deadline_at,
            drawn_at=drawn_at,
            target_member_count=target_count,
            next_excluded_place_ids=next_excluded_place_ids,
            remaining_drawable_place_count=remaining_drawable_place_count,
            can_redraw=remaining_drawable_place_count > 0,
        )
    except (
        PlanNoDrawablePlaceException,
        PlanRoomNotFoundException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanDrawFailedException() from exc


def create_plan(db: Session, *, user_id: UUID, request: CreatePlanRequest | None) -> CreatePlanResponse:
    if request is None:
        raise PlanRequestBodyMissingException()

    room_id = _parse_room_id(request.room_id)
    place_id = _parse_place_id(request.place_id)
    scheduled_at = _parse_datetime(
        request.scheduled_at,
        missing_exception=PlanScheduledAtMissingException,
        invalid_exception=PlanScheduledAtInvalidException,
    )
    response_deadline_at = _parse_datetime(
        request.response_deadline_at,
        missing_exception=PlanResponseDeadlineMissingException,
        invalid_exception=PlanResponseDeadlineInvalidException,
    )
    current_time = _now()
    if scheduled_at <= current_time:
        raise PlanScheduledAtPastException()
    if response_deadline_at <= current_time:
        raise PlanResponseDeadlinePastException()
    if response_deadline_at >= scheduled_at:
        raise PlanResponseDeadlineAfterScheduleException()

    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=room_id, user_id=user_id)
        place = find_place_in_room(db=db, place_id=place_id, room_id=room_id)
        if place is None:
            raise PlanPlaceNotFoundException()

        if find_active_plan_for_place(db=db, room_id=room_id, place_id=place_id) is not None:
            raise PlanAlreadyExistsException()

        target_count = count_target_members(db=db, room_id=room_id, excluded_user_id=user_id)
        if target_count == 0:
            raise PlanTargetMemberMissingException()

        plan = create_plan_row(
            db=db,
            room_id=room_id,
            place_id=place_id,
            creator_id=user_id,
            name=place.title,
            start_time=scheduled_at,
            voting_ends_at=response_deadline_at,
        )
        target_rows = find_target_member_previews(
            db=db,
            room_id=room_id,
            excluded_user_id=user_id,
            limit=None,
        )
        target_user_ids = [row[0] for row in target_rows]
        notification_title = "새 약속 후보가 도착했어요"
        notification_content = f"{place.title}에 같이 갈지 알려주세요."
        notifications = create_notifications(
            db=db,
            user_ids=target_user_ids,
            notification_type=NotificationType.PLAN_REQUESTED,
            title=notification_title,
            content=notification_content,
            target_type=NotificationTargetType.PLAN,
            target_id=plan.id,
        )
        push_payloads = _build_push_payloads(
            notifications=notifications,
            title=notification_title,
            body=notification_content,
        )
        db.commit()
        push_summary = _to_push_summary(
            dispatch_fcm_push_notifications(db=db, payloads=push_payloads)
        )

        return CreatePlanResponse(
            plan_id=plan.id,
            room_id=room_id,
            plan_status=_plan_status_value(plan),
            scheduled_at=plan.start_time,
            response_deadline_at=plan.voting_ends_at,
            target_member_count=target_count,
            target_members=[_build_user_preview(*row) for row in target_rows],
            notification_created_count=len(notifications),
            push_notification=push_summary,
            created_at=plan.created_at,
        )
    except (
        PlanRoomNotFoundException,
        PlanRoomAccessDeniedException,
        PlanPlaceNotFoundException,
        PlanPlaceNotInRoomException,
        PlanAlreadyExistsException,
        PlanTargetMemberMissingException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanCreateFailedException() from exc


def get_plan_responses(db: Session, *, user_id: UUID, plan_id: object) -> PlanResponsesResponse:
    parsed_plan_id = _parse_plan_id(plan_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        plan = _ensure_plan_accessible(db=db, plan_id=parsed_plan_id, user_id=user_id)
        plan, place, _, _, _ = _get_plan_context(db=db, plan_id=plan.id)
        votes = find_votes_by_plan_id(db=db, plan_id=plan.id)
        vote_map = {vote.user_id: vote.is_attending for vote in votes}
        member_rows = find_room_member_response_rows(
            db=db,
            room_id=plan.room_id,
            excluded_user_id=plan.creator_id,
        )
        members = [
            PlanMemberResponse(
                user_id=member_id,
                nickname=nickname,
                profile_image_url=profile_image_url,
                response_status=_response_status_from_vote(vote_map.get(member_id)),
            )
            for member_id, nickname, profile_image_url, _ in member_rows
        ]
        summary = _build_response_summary(
            target_member_count=len(member_rows),
            votes=votes,
        )
        return PlanResponsesResponse(
            server_time=_now(),
            plan=_build_plan_info(plan),
            place=_build_place_summary(place),
            response_summary=summary,
            members=members,
        )
    except (
        PlanNotFoundException,
        PlanDeletedException,
        PlanRoomAccessDeniedException,
        PlanRoomNotFoundException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanResponsesLookupFailedException() from exc


def send_pending_reminders(db: Session, *, user_id: UUID, plan_id: object) -> ReminderResponse:
    parsed_plan_id = _parse_plan_id(plan_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        plan = _ensure_plan_accessible(db=db, plan_id=parsed_plan_id, user_id=user_id)
        if not _is_host_or_creator(db=db, plan=plan, user_id=user_id):
            raise PlanCloseAccessDeniedException()
        if plan.status != PlanStatus.VOTING:
            raise PlanAlreadyClosedException()
        if plan.voting_ends_at <= _now():
            raise PlanResponseDeadlinePassedException()

        votes = find_votes_by_plan_id(db=db, plan_id=plan.id)
        voted_user_ids = {vote.user_id for vote in votes}
        member_rows = find_room_member_response_rows(
            db=db,
            room_id=plan.room_id,
            excluded_user_id=plan.creator_id,
        )
        pending_user_ids = [member_id for member_id, _, _, _ in member_rows if member_id not in voted_user_ids]
        if not pending_user_ids:
            raise PlanPendingMemberNotFoundException()

        notification_title = "응답이 곧 마감돼요"
        notification_content = "아직 응답하지 않은 약속이 있어요."
        notifications = create_notifications(
            db=db,
            user_ids=pending_user_ids,
            notification_type=NotificationType.RESPONSE_DEADLINE_SOON,
            title=notification_title,
            content=notification_content,
            target_type=NotificationTargetType.PLAN,
            target_id=plan.id,
        )
        push_payloads = _build_push_payloads(
            notifications=notifications,
            title=notification_title,
            body=notification_content,
        )
        db.commit()
        push_summary = _to_push_summary(
            dispatch_fcm_push_notifications(db=db, payloads=push_payloads)
        )
        return ReminderResponse(
            plan_id=plan.id,
            pending_count=len(pending_user_ids),
            notification_created_count=len(notifications),
            push_notification=push_summary,
        )
    except (
        PlanCloseAccessDeniedException,
        PlanAlreadyClosedException,
        PlanResponseDeadlinePassedException,
        PlanPendingMemberNotFoundException,
        PlanNotFoundException,
        PlanDeletedException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanReminderFailedException() from exc


def _build_ticket(plan: Plan, place: Place | None, participants: list[PlanUserPreviewResponse]) -> TicketResponse:
    ticket_id = f"MOHAENG-{plan.start_time.astimezone(KST).strftime('%m%d-%H%M')}"
    return TicketResponse(
        ticket_id=ticket_id,
        title=place.title if place else plan.name,
        address=place.location if place else None,
        scheduled_at=plan.start_time,
        participant_count=len(participants),
        participants=participants,
        barcode_value=ticket_id,
        share_url=f"https://example.com/tickets/{ticket_id}",
    )


def close_plan(db: Session, *, user_id: UUID, plan_id: object) -> ClosePlanResponse:
    parsed_plan_id = _parse_plan_id(plan_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        plan = _ensure_plan_accessible(db=db, plan_id=parsed_plan_id, user_id=user_id)
        if not _is_host_or_creator(db=db, plan=plan, user_id=user_id):
            raise PlanCloseAccessDeniedException()
        if plan.status != PlanStatus.VOTING:
            raise PlanAlreadyClosedException()

        votes = find_votes_by_plan_id(db=db, plan_id=plan.id)
        attending_user_ids = [vote.user_id for vote in votes if vote.is_attending]
        if not attending_user_ids:
            raise PlanNoAttendingMemberException()

        participant_ids = []
        if plan.creator_id is not None:
            participant_ids.append(plan.creator_id)
        participant_ids.extend(user_id for user_id in attending_user_ids if user_id not in participant_ids)
        participant_rows = find_members_by_ids(db=db, user_ids=participant_ids)
        participants = [_build_user_preview(*row) for row in participant_rows]

        plan.status = PlanStatus.CONFIRMED
        plan.confirmed_at = _now()
        plan, place, _, _, _ = _get_plan_context(db=db, plan_id=plan.id)
        notify_user_ids = [participant.user_id for participant in participants if participant.user_id and participant.user_id != user_id]
        notification_title = "약속이 확정됐어요"
        notification_content = f"{place.title if place else plan.name} 약속이 확정됐어요."
        notifications = create_notifications(
            db=db,
            user_ids=notify_user_ids,
            notification_type=NotificationType.PLAN_CONFIRMED,
            title=notification_title,
            content=notification_content,
            target_type=NotificationTargetType.PLAN,
            target_id=plan.id,
        )
        push_payloads = _build_push_payloads(
            notifications=notifications,
            title=notification_title,
            body=notification_content,
        )
        db.flush()
        db.commit()
        push_summary = _to_push_summary(
            dispatch_fcm_push_notifications(db=db, payloads=push_payloads)
        )

        return ClosePlanResponse(
            plan_id=plan.id,
            room_id=plan.room_id,
            confirmed_at=plan.confirmed_at,
            ticket=_build_ticket(plan, place, participants),
            notification_created_count=len(notifications),
            push_notification=push_summary,
        )
    except (
        PlanCloseAccessDeniedException,
        PlanAlreadyClosedException,
        PlanNoAttendingMemberException,
        PlanNotFoundException,
        PlanDeletedException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanCloseFailedException() from exc


def get_plan_list(
    db: Session,
    *,
    user_id: UUID,
    room_id: object,
    status: str | None,
    page: object,
    size: object,
) -> PlanListResponse:
    parsed_room_id = _parse_room_id(room_id)
    normalized_status, statuses = _parse_status_filter(status)
    parsed_page = _parse_page(page)
    parsed_size = _parse_size(size)

    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=parsed_room_id, user_id=user_id)
        list_statuses = list(statuses) if statuses is not None else list(PLAN_LIST_VISIBLE_STATUSES)
        total_count = sum(
            count_plans_by_status(db=db, room_id=parsed_room_id, status=status_value)
            for status_value in PLAN_LIST_VISIBLE_STATUSES
        )
        filtered_count = total_count if statuses is None else sum(
            count_plans_by_status(db=db, room_id=parsed_room_id, status=status_value)
            for status_value in list_statuses
        )
        confirmed_count = count_plans_by_status(db=db, room_id=parsed_room_id, status=PlanStatus.CONFIRMED)
        recruiting_count = count_plans_by_status(db=db, room_id=parsed_room_id, status=PlanStatus.VOTING)
        rows = find_plan_list_rows(
            db=db,
            room_id=parsed_room_id,
            statuses=list_statuses,
            offset=parsed_page * parsed_size,
            limit=parsed_size,
        )
        total_pages = ceil(filtered_count / parsed_size) if filtered_count else 0
        items = []
        for plan, place in rows:
            my_vote = find_vote_by_plan_and_user(db=db, plan_id=plan.id, user_id=user_id)
            is_creator = plan.creator_id == user_id
            if plan.status == PlanStatus.CONFIRMED or plan.status == PlanStatus.COMPLETED:
                entry_view_type = ENTRY_VIEW_TICKET
            elif is_creator:
                entry_view_type = ENTRY_VIEW_STATUS
            elif my_vote is None:
                entry_view_type = ENTRY_VIEW_RESPONSE
            else:
                entry_view_type = ENTRY_VIEW_CHANGE_RESPONSE

            items.append(
                PlanListItemResponse(
                    plan_id=plan.id,
                    plan_status=_plan_status_value(plan),
                    title=plan.name or (place.title if place else None),
                    place=_build_place_summary(place),
                    scheduled_at=plan.start_time,
                    response_deadline_at=plan.voting_ends_at if plan.status == PlanStatus.VOTING else None,
                    my_role="HOST" if is_creator else "PARTICIPANT",
                    my_response_status=None if is_creator else _response_status_from_vote(my_vote.is_attending if my_vote else None),
                    entry_view_type=entry_view_type,
                    created_at=plan.created_at,
                    confirmed_at=plan.confirmed_at,
                )
            )

        return PlanListResponse(
            room_id=parsed_room_id,
            status=normalized_status,
            summary=PlanListSummaryResponse(
                total_count=total_count,
                confirmed_count=confirmed_count,
                recruiting_count=recruiting_count,
            ),
            plans=items,
            page_info=PlanPageInfoResponse(
                page=parsed_page,
                size=parsed_size,
                total_elements=filtered_count,
                total_pages=total_pages,
                has_next=parsed_page + 1 < total_pages,
            ),
        )
    except (
        PlanStatusFilterInvalidException,
        PlanRoomNotFoundException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanListLookupFailedException() from exc


def get_invitation(db: Session, *, user_id: UUID, plan_id: object) -> InvitationResponse:
    parsed_plan_id = _parse_plan_id(plan_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        plan = _ensure_plan_accessible(db=db, plan_id=parsed_plan_id, user_id=user_id)
        plan, place, _, creator_nickname, creator_profile_image_url = _get_plan_context(db=db, plan_id=plan.id)
        if plan.status != PLAN_RESPONSE_OPEN_STATUS:
            raise PlanAlreadyClosedException()
        if plan.creator_id == user_id:
            raise PlanResponseAccessDeniedException()
        votes = find_votes_by_plan_id(db=db, plan_id=plan.id)
        my_vote = find_vote_by_plan_and_user(db=db, plan_id=plan.id, user_id=user_id)
        member_rows = find_room_member_response_rows(db=db, room_id=plan.room_id, excluded_user_id=plan.creator_id)
        going_user_ids = [vote.user_id for vote in votes if vote.is_attending]
        going_rows = find_members_by_ids(db=db, user_ids=going_user_ids)
        going_members = [_build_user_preview(*row) for row in going_rows]
        return InvitationResponse(
            plan_id=plan.id,
            room_id=plan.room_id,
            plan_status=_plan_status_value(plan),
            proposed_by=_build_user_basic(plan.creator_id, creator_nickname),
            place=_build_invitation_place(place),
            scheduled_at=plan.start_time,
            response_deadline_at=plan.voting_ends_at,
            server_time=_now(),
            going_member_count=len(going_members),
            going_members=going_members,
            my_response_status=_response_status_from_vote(my_vote.is_attending if my_vote else None),
        )
    except (
        PlanResponseAccessDeniedException,
        PlanAlreadyClosedException,
        PlanNotFoundException,
        PlanDeletedException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanInvitationLookupFailedException() from exc


def save_plan_response(
    db: Session,
    *,
    user_id: UUID,
    plan_id: object,
    request: SavePlanResponseRequest | None,
) -> SavePlanResponseResponse:
    if request is None:
        raise PlanRequestBodyMissingException()
    parsed_plan_id = _parse_plan_id(plan_id)
    is_attending = _parse_response_status(request.response_status)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        plan = _ensure_plan_accessible(db=db, plan_id=parsed_plan_id, user_id=user_id)
        if plan.creator_id == user_id:
            raise PlanResponseAccessDeniedException()
        if plan.status != PlanStatus.VOTING:
            raise PlanAlreadyClosedException()
        if plan.voting_ends_at <= _now():
            raise PlanResponseDeadlinePassedException()

        vote = upsert_vote(db=db, plan_id=plan.id, user_id=user_id, is_attending=is_attending)
        push_payloads: list[FcmPushPayload] = []
        if is_attending and plan.creator_id is not None:
            user = find_user_by_id(db=db, user_id=user_id)
            notification_title = f"{user.nickname if user else '친구'}도 간대요"
            notification_content = "같이 가는 친구가 늘었어요."
            notifications = create_notifications(
                db=db,
                user_ids=[plan.creator_id],
                notification_type=NotificationType.MEMBER_GOING,
                title=notification_title,
                content=notification_content,
                target_type=NotificationTargetType.VOTE,
                target_id=vote.id,
            )
            push_payloads = _build_push_payloads(
                notifications=notifications,
                title=notification_title,
                body=notification_content,
            )
        db.commit()
        if push_payloads:
            dispatch_fcm_push_notifications(db=db, payloads=push_payloads)
        return SavePlanResponseResponse(
            plan=SavedPlanInfoResponse(
                plan_id=plan.id,
                scheduled_at=plan.start_time,
            ),
            my_response={
                "responseStatus": RESPONSE_GOING if is_attending else RESPONSE_NOT_GOING,
            },
        )
    except (
        PlanResponseAccessDeniedException,
        PlanAlreadyClosedException,
        PlanResponseDeadlinePassedException,
        PlanNotFoundException,
        PlanDeletedException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanResponseSaveFailedException() from exc


def get_ticket(db: Session, *, user_id: UUID, plan_id: object) -> TicketLookupResponse:
    parsed_plan_id = _parse_plan_id(plan_id)
    try:
        _ensure_active_user(db=db, user_id=user_id)
        plan = _ensure_plan_accessible(db=db, plan_id=parsed_plan_id, user_id=user_id)
        if plan.status not in {PlanStatus.CONFIRMED, PlanStatus.COMPLETED}:
            raise PlanTicketNotConfirmedException()
        plan, place, _, _, _ = _get_plan_context(db=db, plan_id=plan.id)
        votes = find_votes_by_plan_id(db=db, plan_id=plan.id)
        attending_user_ids = [vote.user_id for vote in votes if vote.is_attending]
        participant_ids = []
        if plan.creator_id is not None:
            participant_ids.append(plan.creator_id)
        participant_ids.extend(member_id for member_id in attending_user_ids if member_id not in participant_ids)
        participants = [_build_user_preview(*row) for row in find_members_by_ids(db=db, user_ids=participant_ids)]
        confirmed_at = plan.confirmed_at or plan.updated_at
        return TicketLookupResponse(
            plan_id=plan.id,
            room_id=plan.room_id,
            confirmed_at=confirmed_at,
            ticket=_build_ticket(plan, place, participants),
        )
    except (
        PlanTicketNotConfirmedException,
        PlanNotFoundException,
        PlanDeletedException,
        PlanRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanTicketLookupFailedException() from exc
