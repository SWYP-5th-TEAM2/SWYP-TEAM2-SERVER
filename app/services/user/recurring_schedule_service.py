import re
from collections import defaultdict
from datetime import datetime, time, timezone
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    RecurringScheduleCreateFailedException,
    RecurringScheduleDayInvalidException,
    RecurringScheduleDaysDuplicatedException,
    RecurringScheduleDaysMissingException,
    RecurringScheduleDeleteFailedException,
    RecurringScheduleEndTimeMissingException,
    RecurringScheduleIdInvalidException,
    RecurringScheduleListFailedException,
    RecurringScheduleNotFoundException,
    RecurringScheduleRequestBodyMissingException,
    RecurringScheduleStartTimeMissingException,
    RecurringScheduleTimeInvalidException,
    RecurringScheduleTimeRangeInvalidException,
    RecurringScheduleTitleMissingException,
    RecurringScheduleTitleTooLongException,
    RecurringScheduleUpdateFailedException,
    RecurringScheduleUpdateFieldsMissingException,
    RecurringScheduleUserNotFoundException,
)
from app.models import DayOfWeek
from app.models.user.enums import UserAccountStatus
from app.repository.schedule import (
    create_recurring_schedule as create_recurring_schedule_record,
    find_recurring_schedule_days_by_group_ids,
    find_recurring_schedule_group_by_id,
    find_recurring_schedule_groups_by_user_id,
    replace_recurring_schedule_days,
    soft_delete_recurring_schedule,
)
from app.repository.user import find_user_by_id
from app.schemas.user import (
    CreateRecurringScheduleRequest,
    RecurringScheduleListResponse,
    RecurringScheduleMutationResponse,
    RecurringScheduleResponse,
    UpdateRecurringScheduleRequest,
)

MAX_RECURRING_SCHEDULE_TITLE_LENGTH = 12
# API 시간 입력은 초 없이 24시간제 HH:MM 형식만 허용한다.
TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
# DB 조회 순서와 관계없이 응답 요일을 월요일부터 일요일 순서로 고정한다.
DAY_ORDER = {day: index for index, day in enumerate(DayOfWeek)}


def _ensure_active_user(db: Session, user_id: UUID) -> None:
    # 실제 사용자 확인
    user = find_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise RecurringScheduleUserNotFoundException()

    # 탈퇴, 비활성화, 차단 계정은 접근 불가
    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()


def _parse_recurring_schedule_id(recurring_schedule_id: str) -> UUID:
    # Path parameter를 문자열로 받아 FastAPI 기본 422 대신 명세의 400 예외로 변환한다.
    try:
        return UUID(recurring_schedule_id)
    except (TypeError, ValueError):
        raise RecurringScheduleIdInvalidException()


def _validate_title(title: str | None) -> str:
    # 제목 누락 - null, 빈 문자열, 공백 문자열
    if title is None or not title.strip():
        raise RecurringScheduleTitleMissingException()

    # 최대 12자 검증
    if len(title) > MAX_RECURRING_SCHEDULE_TITLE_LENGTH:
        raise RecurringScheduleTitleTooLongException()

    return title


def _parse_days_of_week(days_of_week: list[str] | None) -> list[DayOfWeek]:
    # 요일 필수 선택
    if not days_of_week:
        raise RecurringScheduleDaysMissingException()

    # 문자열 -> ENUM
    try:
        parsed_days = [DayOfWeek(day) for day in days_of_week]
    except (TypeError, ValueError):
        raise RecurringScheduleDayInvalidException()

    # 요일 중복 차단
    if len(set(parsed_days)) != len(parsed_days):
        raise RecurringScheduleDaysDuplicatedException()

    return sorted(parsed_days, key=DAY_ORDER.get)


def _parse_time(value: str | None, *, is_start_time: bool) -> time:
    if value is None or not value.strip():
        if is_start_time:
            raise RecurringScheduleStartTimeMissingException()
        raise RecurringScheduleEndTimeMissingException()

    # 정규식 검증 후 Python time으로 변환
    if TIME_PATTERN.fullmatch(value) is None:
        raise RecurringScheduleTimeInvalidException()

    return time.fromisoformat(value)


def _validate_time_range(start_time: time, end_time: time) -> None:
    # 같은 날짜 내 start < end만 허용
    if start_time >= end_time:
        raise RecurringScheduleTimeRangeInvalidException()


def get_recurring_schedules(
    db: Session,
    *,
    user_id: UUID,
) -> RecurringScheduleListResponse:
    try:
        _ensure_active_user(db, user_id)

        # 현재 사용자의 삭제되지 않은 반복 일정 그룹을 조회
        recurring_schedules = find_recurring_schedule_groups_by_user_id(
            db=db,
            user_id=user_id,
        )

        # 모든 그룹의 요일을 한 번에 가져와 그룹마다 조회하는 N+1을 방지
        schedule_days = find_recurring_schedule_days_by_group_ids(
            db=db,
            recurring_schedule_group_ids=[
                recurring_schedule.id
                for recurring_schedule in recurring_schedules
            ],
        )

        # 그룹별 목록으로 변환한다.
        days_by_group_id: dict[UUID, list[DayOfWeek]] = defaultdict(list)
        for recurring_schedule_group_id, day_of_week in schedule_days:
            days_by_group_id[recurring_schedule_group_id].append(day_of_week)

        # DB time은 HH:MM 문자열로, is_enabled는 API의 isActive 필드로 변환된다.
        return RecurringScheduleListResponse(
            recurring_schedules=[
                RecurringScheduleResponse(
                    recurring_schedule_group_id=recurring_schedule.id,
                    title=recurring_schedule.title,
                    days_of_week=sorted(
                        days_by_group_id[recurring_schedule.id],
                        key=DAY_ORDER.get,
                    ),
                    start_time=recurring_schedule.start_time.strftime("%H:%M"),
                    end_time=recurring_schedule.end_time.strftime("%H:%M"),
                    is_active=recurring_schedule.is_enabled,
                )
                for recurring_schedule in recurring_schedules
            ],
        )
    except SQLAlchemyError as exc:
        raise RecurringScheduleListFailedException() from exc


def create_recurring_schedule(
    db: Session,
    *,
    user_id: UUID,
    request: CreateRecurringScheduleRequest | None,
) -> RecurringScheduleMutationResponse:
    if request is None:
        raise RecurringScheduleRequestBodyMissingException()

    title = _validate_title(request.title)
    days_of_week = _parse_days_of_week(request.days_of_week)
    start_time = _parse_time(request.start_time, is_start_time=True)
    end_time = _parse_time(request.end_time, is_start_time=False)
    _validate_time_range(start_time, end_time)

    try:
        _ensure_active_user(db, user_id)

        recurring_schedule = create_recurring_schedule_record(
            db=db,
            user_id=user_id,
            title=title,
            days_of_week=days_of_week,
            start_time=start_time,
            end_time=end_time,
        )

        recurring_schedule_id = recurring_schedule.id
        db.commit()

        return RecurringScheduleMutationResponse(
            recurring_schedule_id=recurring_schedule_id,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise RecurringScheduleCreateFailedException() from exc


def update_recurring_schedule(
    db: Session,
    *,
    user_id: UUID,
    recurring_schedule_id: str,
    request: UpdateRecurringScheduleRequest | None,
) -> RecurringScheduleMutationResponse:
    parsed_schedule_id = _parse_recurring_schedule_id(recurring_schedule_id)

    if request is None:
        raise RecurringScheduleRequestBodyMissingException()

    # PATCH는 일부 필드만 허용하지만 빈 객체는 거부
    provided_fields = request.model_fields_set
    if not provided_fields:
        raise RecurringScheduleUpdateFieldsMissingException()

    title = (
        _validate_title(request.title)
        if "title" in provided_fields
        else None
    )
    days_of_week = (
        _parse_days_of_week(request.days_of_week)
        if "days_of_week" in provided_fields
        else None
    )
    start_time = (
        _parse_time(request.start_time, is_start_time=True)
        if "start_time" in provided_fields
        else None
    )
    end_time = (
        _parse_time(request.end_time, is_start_time=False)
        if "end_time" in provided_fields
        else None
    )

    try:
        _ensure_active_user(db, user_id)

        # ID와 user_id를 함께 조회
        recurring_schedule = find_recurring_schedule_group_by_id(
            db=db,
            user_id=user_id,
            recurring_schedule_id=parsed_schedule_id,
        )
        if recurring_schedule is None:
            raise RecurringScheduleNotFoundException()

        # 시작/종료 중 하나만 전달된 경우 기존 반대편 시간과 조합해 범위 검증
        next_start_time = start_time or recurring_schedule.start_time
        next_end_time = end_time or recurring_schedule.end_time
        _validate_time_range(next_start_time, next_end_time)

        # 값이 전달된 속성만 변경
        if title is not None:
            recurring_schedule.title = title
        if start_time is not None:
            recurring_schedule.start_time = start_time
        if end_time is not None:
            recurring_schedule.end_time = end_time
        if days_of_week is not None:
            # 요일 배열은 기존 행을 부분 수정하지 않고 전체 교체
            replace_recurring_schedule_days(
                db=db,
                recurring_schedule_group_id=recurring_schedule.id,
                days_of_week=days_of_week,
            )

        updated_schedule_id = recurring_schedule.id
        db.commit()

        return RecurringScheduleMutationResponse(
            recurring_schedule_id=updated_schedule_id,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise RecurringScheduleUpdateFailedException() from exc


def delete_recurring_schedule(
    db: Session,
    *,
    user_id: UUID,
    recurring_schedule_id: str,
) -> None:
    parsed_schedule_id = _parse_recurring_schedule_id(recurring_schedule_id)

    try:
        _ensure_active_user(db, user_id)

        recurring_schedule = find_recurring_schedule_group_by_id(
            db=db,
            user_id=user_id,
            recurring_schedule_id=parsed_schedule_id,
        )
        if recurring_schedule is None:
            raise RecurringScheduleNotFoundException()

        # deleted_at 기록
        soft_delete_recurring_schedule(
            recurring_schedule,
            deleted_at=datetime.now(timezone.utc),
        )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise RecurringScheduleDeleteFailedException() from exc
