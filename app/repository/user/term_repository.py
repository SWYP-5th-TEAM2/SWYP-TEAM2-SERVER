import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Term, UserTermsAgreements


def find_active_terms(db: Session) -> list[Term]:
    stmt = (
        select(Term)
        .where(
            Term.is_active.is_(True),
            Term.deleted_at.is_(None),
        )
        .order_by(Term.created_at.asc(), Term.id.asc())
    )

    return list(db.execute(stmt).scalars().all())


def find_active_user_term_agreement_ids(
    db: Session,
    *,
    user_id: UUID,
    term_ids: list[UUID],
) -> set[UUID]:
    if not term_ids:
        return set()

    stmt = select(UserTermsAgreements.term_id).where(
        UserTermsAgreements.user_id == user_id,
        UserTermsAgreements.term_id.in_(term_ids),
        UserTermsAgreements.revoked_at.is_(None),
        UserTermsAgreements.deleted_at.is_(None),
    )

    return set(db.execute(stmt).scalars().all())


def create_user_terms_agreements(
    db: Session,
    *,
    user_id: UUID,
    term_ids: list[UUID],
) -> None:
    if not term_ids:
        return

    agreed_at = datetime.now(timezone.utc)
    stmt = insert(UserTermsAgreements).values(
        [
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "term_id": term_id,
                "agreed_at": agreed_at,
            }
            for term_id in term_ids
        ]
    ).on_conflict_do_nothing(
        index_elements=["user_id", "term_id"],
        index_where=(
            UserTermsAgreements.revoked_at.is_(None)
            & UserTermsAgreements.deleted_at.is_(None)
        ),
    )

    db.execute(stmt)
