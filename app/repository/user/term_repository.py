from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Term


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
