from app.models.user.enums import TermType
from app.schemas.common import CamelModel


class TermResponse(CamelModel):
    type: TermType
    title: str
    is_required: bool
    content_url: str


class TermsListResponse(CamelModel):
    terms: list[TermResponse]
