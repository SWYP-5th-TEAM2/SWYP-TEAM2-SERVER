from pydantic import ConfigDict

from app.schemas.common import CamelModel


class UserWithdrawalRequest(CamelModel):
    withdraw_reason: list[str] | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["withdrawReason"],
            "properties": {
                "withdrawReason": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "RARELY_USE",
                            "MISSING_FEATURES",
                            "DIFFICULT_TO_USE",
                            "NO_TIME_TO_USE",
                            "ETC",
                        ],
                    },
                    "minItems": 1,
                },
            },
        },
    )
