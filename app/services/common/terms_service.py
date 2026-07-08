from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import TermsLookupFailedException, TermsNotFoundException
from app.repository.user import find_active_terms
from app.schemas.terms import TermResponse, TermsListResponse


def get_active_terms(db: Session) -> TermsListResponse:
    try:
        terms = find_active_terms(db)

        if not terms:
            raise TermsNotFoundException()

        return TermsListResponse(
            terms=[
                TermResponse(
                    type=term.type,
                    title=term.title,
                    is_required=term.is_required,
                    content_url=term.content_url,
                )
                for term in terms
            ],
        )
    except TermsNotFoundException:
        raise
    except SQLAlchemyError as exc:
        raise TermsLookupFailedException() from exc
