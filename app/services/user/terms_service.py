from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ForbiddenException,
    RequiredTermsNotAgreedException,
    TermsAgreementFailedException,
    TermsAgreementFieldsMissingException,
    TermsAgreementRequestBodyMissingException,
    UserNotFoundException,
)
from app.models import Term, User
from app.models.user.enums import TermType, UserAccountStatus
from app.repository.user import (
    create_user_terms_agreements,
    find_active_terms,
    find_active_user_term_agreement_ids,
    find_user_by_id,
)
from app.schemas.user import AgreeTermsRequest

TERMS_REQUEST_FIELDS = frozenset({"service", "privacy"})
REQUEST_FIELD_BY_TERM_TYPE = {
    TermType.SERVICE: "service",
    TermType.PRIVACY: "privacy",
}


def _ensure_active_user(db: Session, user_id: UUID) -> User:
    user = find_user_by_id(
        db=db,
        user_id=user_id,
    )

    if user is None:
        raise UserNotFoundException()

    if user.status != UserAccountStatus.ACTIVE:
        raise ForbiddenException()

    return user


def _validate_request(request: AgreeTermsRequest | None) -> None:
    if request is None:
        raise TermsAgreementRequestBodyMissingException()

    provided_fields = request.model_fields_set & TERMS_REQUEST_FIELDS
    if provided_fields != TERMS_REQUEST_FIELDS:
        raise TermsAgreementFieldsMissingException()

    for field_name in TERMS_REQUEST_FIELDS:
        if type(getattr(request, field_name)) is not bool:
            raise TermsAgreementFieldsMissingException()


# request key -> enum
def _get_requested_agreement(request: AgreeTermsRequest, term: Term) -> bool:
    field_name = REQUEST_FIELD_BY_TERM_TYPE[term.type]
    return getattr(request, field_name)


def agree_terms(
    db: Session,
    *,
    user_id: UUID,
    request: AgreeTermsRequest | None,
) -> None:
    _validate_request(request)
    assert request is not None

    try:
        _ensure_active_user(db, user_id)

        active_terms = find_active_terms(db)
        if not active_terms:
            raise TermsAgreementFailedException()

        required_terms = [term for term in active_terms if term.is_required]
        if any(not _get_requested_agreement(request, term) for term in required_terms):
            raise RequiredTermsNotAgreedException()

        agreed_terms = [
            term
            for term in active_terms
            if _get_requested_agreement(request, term)
        ]
        agreed_term_ids = [term.id for term in agreed_terms]
        # 이미 동의한 내역 확인
        existing_term_ids = find_active_user_term_agreement_ids(
            db=db,
            user_id=user_id,
            term_ids=agreed_term_ids,
        )

        new_term_ids = [
            term_id
            for term_id in agreed_term_ids
            if term_id not in existing_term_ids
        ]

        if new_term_ids:
            create_user_terms_agreements(
                db=db,
                user_id=user_id,
                term_ids=new_term_ids,
            )

        db.commit()
    except (
        ForbiddenException,
        RequiredTermsNotAgreedException,
        TermsAgreementFailedException,
        UserNotFoundException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise TermsAgreementFailedException() from exc
