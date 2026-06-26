"""apply latest erd models

Revision ID: 8f0c2b1a7d3e
Revises: 191452b9771b
Create Date: 2026-06-26 00:00:00.000000+09:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8f0c2b1a7d3e"
down_revision: Union[str, None] = "191452b9771b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "images",
        sa.Column("id", sa.UUID(), nullable=False, comment="이미지 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="업로드 사용자 ID"),
        sa.Column("image_url", sa.String(length=2048), nullable=False, comment="이미지 저장 URL"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="이미지 파일명"),
        sa.Column("file_size", sa.BigInteger(), nullable=False, comment="이미지 파일 크기(byte)"),
        sa.Column("content_type", sa.String(length=50), nullable=False, comment="이미지 파일 형식"),
        sa.Column(
            "image_purpose",
            sa.Enum("PROFILE_IMAGE", "SOURCE", "PLACE", name="image_purpose"),
            nullable=False,
            comment="이미지 사용 목적",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_images_user_id"), "images", ["user_id"], unique=False)

    op.add_column(
        "users",
        sa.Column("profile_image_id", sa.UUID(), nullable=True, comment="프로필 이미지 ID"),
    )
    op.create_foreign_key(
        "fk_users_profile_image_id",
        "users",
        "images",
        ["profile_image_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_column("users", "birthday")
    op.drop_column("users", "gender")
    postgresql.ENUM(name="gender").drop(op.get_bind(), checkfirst=True)

    op.create_table(
        "rooms",
        sa.Column("id", sa.UUID(), nullable=False, comment="방 ID"),
        sa.Column("name", sa.String(length=30), nullable=False, comment="방 이름"),
        sa.Column("color", sa.String(length=20), nullable=False, comment="방 폴더 색상"),
        sa.Column("invite_code", sa.String(length=6), nullable=False, comment="초대 코드"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_code", name="uq_rooms_invite_code"),
    )
    op.create_index(op.f("ix_rooms_invite_code"), "rooms", ["invite_code"], unique=False)

    op.create_table(
        "room_members",
        sa.Column("id", sa.UUID(), nullable=False, comment="방 가입자 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="사용자 ID"),
        sa.Column("room_id", sa.UUID(), nullable=False, comment="방 ID"),
        sa.Column(
            "role",
            sa.Enum("HOST", "MEMBER", name="room_member_role"),
            server_default="MEMBER",
            nullable=False,
            comment="방 멤버 역할",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "user_id", name="uq_room_members_room_user"),
    )
    op.create_index(op.f("ix_room_members_room_id"), "room_members", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_members_user_id"), "room_members", ["user_id"], unique=False)

    op.create_table(
        "recurring_schedule_groups",
        sa.Column("id", sa.UUID(), nullable=False, comment="반복 일정 그룹 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="사용자 ID"),
        sa.Column("title", sa.String(length=50), nullable=False, comment="반복 일정 사유"),
        sa.Column("is_enabled", sa.Boolean(), server_default="false", nullable=False, comment="활성화 여부"),
        sa.Column("start_time", sa.Time(), nullable=False, comment="시작 시간"),
        sa.Column("end_time", sa.Time(), nullable=False, comment="종료 시간"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recurring_schedule_groups_user_id"), "recurring_schedule_groups", ["user_id"], unique=False)

    op.create_table(
        "recurring_schedule_day",
        sa.Column("id", sa.UUID(), nullable=False, comment="반복 일정 요일 ID"),
        sa.Column("recurring_schedule_group_id", sa.UUID(), nullable=False, comment="반복 일정 그룹 ID"),
        sa.Column(
            "day_of_week",
            sa.Enum("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN", name="day_of_week"),
            nullable=False,
            comment="요일",
        ),
        sa.ForeignKeyConstraint(["recurring_schedule_group_id"], ["recurring_schedule_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recurring_schedule_group_id", "day_of_week", name="uq_recurring_schedule_day_group_day"),
    )
    op.create_index(op.f("ix_recurring_schedule_day_recurring_schedule_group_id"), "recurring_schedule_day", ["recurring_schedule_group_id"], unique=False)

    op.create_table(
        "user_fcm_tokens",
        sa.Column("id", sa.UUID(), nullable=False, comment="FCM 토큰 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="사용자 ID"),
        sa.Column("fcm_token", sa.String(length=512), nullable=False, comment="FCM 토큰"),
        sa.Column(
            "device_type",
            sa.Enum("IOS", "ANDROID", name="device_type"),
            nullable=False,
            comment="사용 기기",
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False, comment="푸시 전송 가능 여부"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fcm_token", name="uq_user_fcm_tokens_fcm_token"),
    )
    op.create_index(op.f("ix_user_fcm_tokens_user_id"), "user_fcm_tokens", ["user_id"], unique=False)

    op.create_table(
        "places",
        sa.Column("id", sa.UUID(), nullable=False, comment="후보 장소 ID"),
        sa.Column("room_id", sa.UUID(), nullable=False, comment="방 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="장소를 등록한 사용자 ID"),
        sa.Column("place_image_id", sa.UUID(), nullable=True, comment="장소 썸네일 이미지 ID"),
        sa.Column("source_image_id", sa.UUID(), nullable=True, comment="소스 이미지 ID"),
        sa.Column(
            "status",
            sa.Enum("READY_TO_DRAW", "NEEDS_EDIT", name="place_status"),
            server_default="READY_TO_DRAW",
            nullable=False,
            comment="장소 상태",
        ),
        sa.Column("title", sa.String(length=50), nullable=False, comment="후보 타이틀"),
        sa.Column("name", sa.String(length=30), nullable=True, comment="장소명"),
        sa.Column("location", sa.String(length=255), nullable=True, comment="장소 위치"),
        sa.Column("latitude", sa.Float(), nullable=True, comment="장소 위도"),
        sa.Column("longitude", sa.Float(), nullable=True, comment="장소 경도"),
        sa.Column("memo", sa.String(length=255), nullable=True, comment="메모"),
        sa.Column("place_image", sa.String(length=2048), nullable=True, comment="장소 썸네일 이미지 URL"),
        sa.Column("source", sa.String(length=100), nullable=True, comment="정보 출처"),
        sa.Column("url", sa.String(length=2048), nullable=True, comment="출처 URL"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["place_image_id"], ["images.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_image_id"], ["images.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_places_room_id"), "places", ["room_id"], unique=False)
    op.create_index(op.f("ix_places_user_id"), "places", ["user_id"], unique=False)

    op.create_table(
        "plans",
        sa.Column("id", sa.UUID(), nullable=False, comment="계획 ID"),
        sa.Column("room_id", sa.UUID(), nullable=True, comment="방 ID"),
        sa.Column("place_id", sa.UUID(), nullable=True, comment="후보 장소 ID"),
        sa.Column("creator_id", sa.UUID(), nullable=True, comment="약속 생성자 ID"),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "VOTING", "CONFIRMED", "COMPLETED", name="plan_status"),
            server_default="DRAFT",
            nullable=False,
            comment="계획 상태",
        ),
        sa.Column("name", sa.String(length=30), nullable=True, comment="약속명"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False, comment="일정 시작 시간"),
        sa.Column("voting_ends_at", sa.DateTime(timezone=True), nullable=False, comment="투표 종료 일시"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True, comment="약속 확정 일시"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["place_id"], ["places.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plans_creator_id"), "plans", ["creator_id"], unique=False)
    op.create_index(op.f("ix_plans_place_id"), "plans", ["place_id"], unique=False)
    op.create_index(op.f("ix_plans_room_id"), "plans", ["room_id"], unique=False)

    op.create_table(
        "votes",
        sa.Column("id", sa.UUID(), nullable=False, comment="일정 투표 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="사용자 ID"),
        sa.Column("plan_id", sa.UUID(), nullable=False, comment="계획 ID"),
        sa.Column("is_attending", sa.Boolean(), nullable=False, comment="참석 여부"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "plan_id", name="uq_votes_user_plan"),
    )
    op.create_index(op.f("ix_votes_plan_id"), "votes", ["plan_id"], unique=False)
    op.create_index(op.f("ix_votes_user_id"), "votes", ["user_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False, comment="알림 ID"),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="알림 수신 사용자 ID"),
        sa.Column(
            "type",
            sa.Enum(
                "PLAN_REQUESTED",
                "PLAN_CONFIRMED",
                "MEMBER_GOING",
                "QUIET_RECOMMENDATION",
                "RESPONSE_DEADLINE_SOON",
                name="notification_type",
            ),
            nullable=False,
            comment="알림 유형",
        ),
        sa.Column("title", sa.String(length=100), nullable=False, comment="알림 제목"),
        sa.Column("content", sa.String(length=255), nullable=False, comment="알림 본문"),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False, comment="읽음 여부"),
        sa.Column(
            "target_type",
            sa.Enum("PLAN", "ROOM", "PLACE", "VOTE", name="notification_target_type"),
            nullable=True,
            comment="알림 이동 대상 유형",
        ),
        sa.Column("target_id", sa.UUID(), nullable=True, comment="알림 이동 대상 ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="생성 일자"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="수정 일자"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="삭제 일자"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_notifications_target_id"), "notifications", ["target_id"], unique=False)
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_target_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_votes_user_id"), table_name="votes")
    op.drop_index(op.f("ix_votes_plan_id"), table_name="votes")
    op.drop_table("votes")

    op.drop_index(op.f("ix_plans_room_id"), table_name="plans")
    op.drop_index(op.f("ix_plans_place_id"), table_name="plans")
    op.drop_index(op.f("ix_plans_creator_id"), table_name="plans")
    op.drop_table("plans")

    op.drop_index(op.f("ix_places_user_id"), table_name="places")
    op.drop_index(op.f("ix_places_room_id"), table_name="places")
    op.drop_table("places")

    op.drop_index(op.f("ix_user_fcm_tokens_user_id"), table_name="user_fcm_tokens")
    op.drop_table("user_fcm_tokens")

    op.drop_index(op.f("ix_recurring_schedule_day_recurring_schedule_group_id"), table_name="recurring_schedule_day")
    op.drop_table("recurring_schedule_day")

    op.drop_index(op.f("ix_recurring_schedule_groups_user_id"), table_name="recurring_schedule_groups")
    op.drop_table("recurring_schedule_groups")

    op.drop_index(op.f("ix_room_members_user_id"), table_name="room_members")
    op.drop_index(op.f("ix_room_members_room_id"), table_name="room_members")
    op.drop_table("room_members")

    op.drop_index(op.f("ix_rooms_invite_code"), table_name="rooms")
    op.drop_table("rooms")

    op.drop_constraint("fk_users_profile_image_id", "users", type_="foreignkey")
    op.drop_column("users", "profile_image_id")

    op.drop_index(op.f("ix_images_user_id"), table_name="images")
    op.drop_table("images")

    gender_enum = postgresql.ENUM("MALE", "FEMALE", name="gender")
    gender_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("gender", gender_enum, nullable=True, comment="성별"))
    op.add_column("users", sa.Column("birthday", sa.Date(), nullable=True, comment="생년월일"))

    postgresql.ENUM(name="notification_target_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="notification_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="plan_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="place_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="device_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="day_of_week").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="room_member_role").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="image_purpose").drop(op.get_bind(), checkfirst=True)
