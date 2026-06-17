from typing import Any

from fastapi.encoders import jsonable_encoder


def success_response(
    data: Any = None,
    message: str = "응답 성공",
    code: str = "SUCCESS",
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": jsonable_encoder(data, by_alias=True),
    }


def error_response(
    code: str,
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": jsonable_encoder(data, by_alias=True),
    }
