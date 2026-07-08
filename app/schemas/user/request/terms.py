from typing import Any

from app.schemas.common import CamelModel


class AgreeTermsRequest(CamelModel):
    service: Any = None
    privacy: Any = None
