from __future__ import annotations

import base64
import json
import re
import time
import uuid
from typing import Any
from uuid import UUID

import httpx
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import (
    ForbiddenException,
    PlaceImageExtractionFailedException,
    PlaceImageExtractionResponseInvalidException,
    PlaceImageExtractionServiceUnavailableException,
    PlaceImageFileMissingException,
    PlaceImageFileSizeExceededException,
    PlaceRoomAccessDeniedException,
    PlaceRoomNotFoundException,
    UnsupportedImageSizeException,
    UserNotFoundException,
)
from app.models import ImagePurpose
from app.schemas.image import ImageUploadResponse
from app.schemas.place import ExtractedPlaceResponse, PlaceImageExtractionResponse
from app.services.common.image_service import _validate_image_file, upload_image
from app.services.place.place.place_service import _ensure_active_user, _ensure_room_member, _parse_room_id

AI_PROVIDER = "GEMINI"
MAX_GEMINI_IMAGE_BYTES = 15 * 1024 * 1024


def _place_extraction_schema() -> dict[str, Any]:
    place_schema = {
        "type": "OBJECT",
        "properties": {
            "placeName": {
                "type": "STRING",
                "nullable": True,
                "description": "Actual place or store name visible in the image. Null if unclear.",
            },
            "address": {
                "type": "STRING",
                "nullable": True,
                "description": "Address, station/exit, landmark, or visible location description. Null if unclear.",
            },
            "latitude": {
                "type": "NUMBER",
                "nullable": True,
                "description": "Latitude only if explicitly visible in the image. Never infer.",
            },
            "longitude": {
                "type": "NUMBER",
                "nullable": True,
                "description": "Longitude only if explicitly visible in the image. Never infer.",
            },
            "notes": {
                "type": "STRING",
                "nullable": True,
                "description": "Short extraction note or uncertainty memo.",
            },
        },
        "required": ["placeName", "address", "latitude", "longitude", "notes"],
    }
    return {
        "type": "OBJECT",
        "properties": {
            "isPlaceInfoFound": {
                "type": "BOOLEAN",
                "description": "True if at least one place/store fact is visible in the image.",
            },
            "extractedPlaces": {
                "type": "ARRAY",
                "items": place_schema,
                "description": "All distinct places found in the image. Empty array if none are found.",
            },
        },
        "required": ["isPlaceInfoFound", "extractedPlaces"],
    }


def _build_prompt() -> str:
    return """
당신은 사용자가 업로드한 이미지에서 장소 후보로 사용할 수 있는 정보를 추출하는 도우미입니다.
OCR 엔진을 별도로 사용하지 않고 이미지 자체를 보고 판단합니다.

규칙:
1. 이미지에서 실제로 보이는 장소 정보만 추출합니다.
2. 실제 장소명(placeName)과 주소 또는 위치 설명(address)을 우선 추출합니다.
3. 위도(latitude), 경도(longitude)는 이미지 안에 숫자로 명확히 적혀 있을 때만 추출합니다.
4. 위도/경도는 절대 추측하거나 생성하지 않습니다. 보이지 않으면 null로 둡니다.
5. 여러 장소가 보이면 extractedPlaces 배열에 모두 담습니다.
6. 장소와 무관한 사람 이름, 계정명, 댓글 작성자, 광고 문구는 장소 정보로 저장하지 않습니다.
7. 불확실한 값은 null로 둡니다.
8. notes에는 추출 결과에 대한 짧은 설명이나 불확실성만 적습니다.
""".strip()


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_response_text(response_payload: dict[str, Any]) -> str:
    try:
        candidates = response_payload["candidates"]
        first = candidates[0]
        parts = first["content"]["parts"]
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
    except (KeyError, IndexError, TypeError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc

    text = "".join(text_parts).strip()
    if not text:
        raise PlaceImageExtractionResponseInvalidException()
    return text


def _normalize_optional_str(value: object) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _normalize_optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload.get(key)
    return None


def _parse_ai_payload(payload: dict[str, Any]) -> list[ExtractedPlaceResponse]:
    raw_places = _get_first_value(payload, "extractedPlaces", "extracted_places", "places")
    if raw_places is None:
        raw_places = []
    if not isinstance(raw_places, list):
        raise PlaceImageExtractionResponseInvalidException()

    places: list[ExtractedPlaceResponse] = []
    seen: set[tuple[str, str]] = set()
    for raw_place in raw_places:
        if not isinstance(raw_place, dict):
            continue
        place_name = _normalize_optional_str(_get_first_value(raw_place, "placeName", "place_name"))
        address = _normalize_optional_str(raw_place.get("address"))
        notes = _normalize_optional_str(raw_place.get("notes"))
        latitude = _normalize_optional_float(raw_place.get("latitude"))
        longitude = _normalize_optional_float(raw_place.get("longitude"))

        if not place_name and not address:
            continue
        key = (
            re.sub(r"\s+", "", place_name or "").lower(),
            re.sub(r"\s+", "", address or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        places.append(
            ExtractedPlaceResponse(
                place_name=place_name,
                address=address,
                latitude=latitude,
                longitude=longitude,
                notes=notes,
            )
        )
    return places


async def _call_gemini_image_extraction(*, image_bytes: bytes, content_type: str) -> list[ExtractedPlaceResponse]:
    api_key = settings.gemini_api_key
    if not api_key or api_key.strip() in {"your-gemini-api-key", "your_gemini_api_key_here"}:
        raise PlaceImageExtractionServiceUnavailableException()
    if len(image_bytes) > MAX_GEMINI_IMAGE_BYTES:
        raise PlaceImageExtractionServiceUnavailableException()

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    request_payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": _build_prompt()},
                    {
                        "inlineData": {
                            "mimeType": content_type,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": _place_extraction_schema(),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.gemini_request_timeout_seconds) as client:
            response = await client.post(url, params={"key": api_key}, json=request_payload)
    except httpx.TimeoutException as exc:
        raise PlaceImageExtractionServiceUnavailableException() from exc
    except httpx.HTTPError as exc:
        raise PlaceImageExtractionServiceUnavailableException() from exc

    if response.status_code >= 500:
        raise PlaceImageExtractionServiceUnavailableException()
    if response.status_code >= 400:
        raise PlaceImageExtractionResponseInvalidException()

    try:
        response_payload = response.json()
        output_text = _strip_json_fence(_extract_response_text(response_payload))
        ai_payload = json.loads(output_text)
        if not isinstance(ai_payload, dict):
            raise TypeError("Gemini response is not an object")
        return _parse_ai_payload(ai_payload)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc


async def extract_place_info_from_image(
    db: Session,
    *,
    user_id: UUID,
    room_id: object,
    file: UploadFile | None,
) -> PlaceImageExtractionResponse:
    parsed_room_id = _parse_room_id(room_id)
    if file is None:
        raise PlaceImageFileMissingException()

    try:
        _ensure_active_user(db=db, user_id=user_id)
        _ensure_room_member(db=db, room_id=parsed_room_id, user_id=user_id)
    except (
        PlaceRoomNotFoundException,
        PlaceRoomAccessDeniedException,
        UserNotFoundException,
        ForbiddenException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceImageExtractionFailedException() from exc

    try:
        _, content_type = await _validate_image_file(file)
    except UnsupportedImageSizeException as exc:
        raise PlaceImageFileSizeExceededException() from exc

    try:
        image_bytes = await file.read()
        await file.seek(0)
        start = time.perf_counter()
        extracted_places = await _call_gemini_image_extraction(
            image_bytes=image_bytes,
            content_type=content_type,
        )
        _ = int((time.perf_counter() - start) * 1000)  # 추후 로그/메트릭 확장용
        uploaded_image: ImageUploadResponse = await upload_image(
            db=db,
            user_id=user_id,
            file=file,
            image_purpose=ImagePurpose.SOURCE.value,
        )
        image_url = str(uploaded_image.image_url)

        return PlaceImageExtractionResponse(
            extraction_id=uuid.uuid4(),
            room_id=parsed_room_id,
            image_url=image_url,
            extracted_places=extracted_places,
        )
    except (
        PlaceImageExtractionResponseInvalidException,
        PlaceImageExtractionServiceUnavailableException,
        PlaceImageFileSizeExceededException,
    ):
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlaceImageExtractionFailedException() from exc
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise PlaceImageExtractionFailedException() from exc
