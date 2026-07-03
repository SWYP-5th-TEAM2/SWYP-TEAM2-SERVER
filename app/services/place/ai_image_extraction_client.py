from __future__ import annotations

import base64
import json
import re
from enum import StrEnum
from typing import Any

import httpx

from app.config import settings
from app.core.exceptions import (
    PlaceImageExtractionResponseInvalidException,
    PlaceImageExtractionServiceUnavailableException,
)
from app.schemas.place import ExtractedPlaceResponse


class ImageExtractionAiProvider(StrEnum):
    GEMINI = "GEMINI"
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"


MAX_IMAGE_BYTES = 15 * 1024 * 1024


PROVIDER_ALIASES = {
    "GEMINI": ImageExtractionAiProvider.GEMINI,
    "GOOGLE": ImageExtractionAiProvider.GEMINI,
    "GOOGLE_GEMINI": ImageExtractionAiProvider.GEMINI,
    "OPENAI": ImageExtractionAiProvider.OPENAI,
    "GPT": ImageExtractionAiProvider.OPENAI,
    "ANTHROPIC": ImageExtractionAiProvider.ANTHROPIC,
    "CLAUDE": ImageExtractionAiProvider.ANTHROPIC,
}


def _is_configured(value: str | None, *, placeholder_prefixes: tuple[str, ...] = ("your-",)) -> bool:
    if value is None:
        return False
    normalized = value.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return not any(lowered.startswith(prefix) for prefix in placeholder_prefixes)


def _selected_provider() -> ImageExtractionAiProvider:
    raw_provider = (settings.image_extraction_ai_provider or "GEMINI").strip().upper()
    provider = PROVIDER_ALIASES.get(raw_provider)
    if provider is None:
        raise PlaceImageExtractionServiceUnavailableException()
    return provider


def _gemini_response_schema() -> dict[str, Any]:
    place_schema = {
        "type": "OBJECT",
        "properties": {
            "placeName": {"type": "STRING", "nullable": True},
            "address": {"type": "STRING", "nullable": True},
            "latitude": {"type": "NUMBER", "nullable": True},
            "longitude": {"type": "NUMBER", "nullable": True},
            "notes": {"type": "STRING", "nullable": True},
        },
        "required": ["placeName", "address", "latitude", "longitude", "notes"],
    }
    return {
        "type": "OBJECT",
        "properties": {
            "isPlaceInfoFound": {"type": "BOOLEAN"},
            "extractedPlaces": {"type": "ARRAY", "items": place_schema},
        },
        "required": ["isPlaceInfoFound", "extractedPlaces"],
    }


def _json_response_schema() -> dict[str, Any]:
    place_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "placeName": {"type": ["string", "null"]},
            "address": {"type": ["string", "null"]},
            "latitude": {"type": ["number", "null"]},
            "longitude": {"type": ["number", "null"]},
            "notes": {"type": ["string", "null"]},
        },
        "required": ["placeName", "address", "latitude", "longitude", "notes"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "isPlaceInfoFound": {"type": "boolean"},
            "extractedPlaces": {"type": "array", "items": place_schema},
        },
        "required": ["isPlaceInfoFound", "extractedPlaces"],
    }


def _build_prompt(*, include_schema: bool = False) -> str:
    prompt = """
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
9. 반드시 JSON 객체만 반환합니다. 설명 문장, 마크다운 코드블록, 주석은 반환하지 않습니다.
""".strip()
    if include_schema:
        schema = json.dumps(_json_response_schema(), ensure_ascii=False)
        prompt += f"\n\n반환 JSON Schema:\n{schema}"
    return prompt


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _load_json_object(text: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match is None:
            raise PlaceImageExtractionResponseInvalidException()
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise PlaceImageExtractionResponseInvalidException() from exc
    if not isinstance(payload, dict):
        raise PlaceImageExtractionResponseInvalidException()
    return payload


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


def _ensure_image_size(image_bytes: bytes) -> None:
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise PlaceImageExtractionServiceUnavailableException()


def _data_url(*, image_bytes: bytes, content_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def _extract_gemini_text(response_payload: dict[str, Any]) -> str:
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


async def _call_gemini(*, image_bytes: bytes, content_type: str) -> list[ExtractedPlaceResponse]:
    api_key = settings.gemini_api_key
    if not _is_configured(api_key):
        raise PlaceImageExtractionServiceUnavailableException()
    _ensure_image_size(image_bytes)

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
            "responseSchema": _gemini_response_schema(),
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.gemini_request_timeout_seconds) as client:
            response = await client.post(url, params={"key": api_key}, json=request_payload)
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        raise PlaceImageExtractionServiceUnavailableException() from exc

    if response.status_code >= 500:
        raise PlaceImageExtractionServiceUnavailableException()
    if response.status_code >= 400:
        raise PlaceImageExtractionResponseInvalidException()

    try:
        response_payload = response.json()
        ai_payload = _load_json_object(_extract_gemini_text(response_payload))
        return _parse_ai_payload(ai_payload)
    except (TypeError, ValueError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc


def _extract_openai_response_text(response_payload: dict[str, Any]) -> str:
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = response_payload.get("output")
    if isinstance(output, list):
        text_parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text") or part.get("output_text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text)
        if text_parts:
            return "".join(text_parts).strip()

    raise PlaceImageExtractionResponseInvalidException()


async def _call_openai_responses(*, image_bytes: bytes, content_type: str) -> list[ExtractedPlaceResponse]:
    api_key = settings.openai_api_key
    model = settings.openai_image_extraction_model
    if not _is_configured(api_key) or not _is_configured(model):
        raise PlaceImageExtractionServiceUnavailableException()
    _ensure_image_size(image_bytes)

    base_url = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
    request_payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": _build_prompt()},
                    {"type": "input_image", "image_url": _data_url(image_bytes=image_bytes, content_type=content_type)},
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "place_image_extraction",
                "strict": True,
                "schema": _json_response_schema(),
            }
        },
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=settings.openai_request_timeout_seconds) as client:
            response = await client.post(f"{base_url}/responses", headers=headers, json=request_payload)
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        raise PlaceImageExtractionServiceUnavailableException() from exc

    if response.status_code >= 500:
        raise PlaceImageExtractionServiceUnavailableException()
    if response.status_code >= 400:
        raise PlaceImageExtractionResponseInvalidException()

    try:
        response_payload = response.json()
        ai_payload = _load_json_object(_extract_openai_response_text(response_payload))
        return _parse_ai_payload(ai_payload)
    except (TypeError, ValueError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc


def _extract_chat_completion_text(response_payload: dict[str, Any]) -> str:
    try:
        choices = response_payload["choices"]
        first = choices[0]
        content = first["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc

    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        text_parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("text")]
        if text_parts:
            return "".join(text_parts).strip()
    raise PlaceImageExtractionResponseInvalidException()


async def _call_openai_chat_completions(*, image_bytes: bytes, content_type: str) -> list[ExtractedPlaceResponse]:
    api_key = settings.openai_api_key
    base_url = settings.openai_base_url
    model = settings.openai_image_extraction_model
    if (
        not _is_configured(api_key)
        or not _is_configured(base_url, placeholder_prefixes=("https://example", "your-"))
        or not _is_configured(model)
    ):
        raise PlaceImageExtractionServiceUnavailableException()
    _ensure_image_size(image_bytes)

    request_payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _build_prompt(include_schema=True)},
                    {
                        "type": "image_url",
                        "image_url": {"url": _data_url(image_bytes=image_bytes, content_type=content_type)},
                    },
                ],
            }
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        async with httpx.AsyncClient(timeout=settings.openai_request_timeout_seconds) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=request_payload,
            )
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        raise PlaceImageExtractionServiceUnavailableException() from exc

    if response.status_code >= 500:
        raise PlaceImageExtractionServiceUnavailableException()
    if response.status_code >= 400:
        raise PlaceImageExtractionResponseInvalidException()

    try:
        response_payload = response.json()
        ai_payload = _load_json_object(_extract_chat_completion_text(response_payload))
        return _parse_ai_payload(ai_payload)
    except (TypeError, ValueError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc


def _should_use_openai_chat_completions() -> bool:
    mode = (settings.openai_api_mode or "AUTO").strip().upper()
    if mode in {"CHAT", "CHAT_COMPLETIONS", "CHAT_COMPLETION"}:
        return True
    if mode in {"RESPONSES", "RESPONSE"}:
        return False
    if mode != "AUTO":
        raise PlaceImageExtractionServiceUnavailableException()

    base_url = (settings.openai_base_url or "").lower()
    return "api.openai.com" not in base_url


async def _call_openai(*, image_bytes: bytes, content_type: str) -> list[ExtractedPlaceResponse]:
    if _should_use_openai_chat_completions():
        return await _call_openai_chat_completions(image_bytes=image_bytes, content_type=content_type)
    return await _call_openai_responses(image_bytes=image_bytes, content_type=content_type)


def _extract_anthropic_text(response_payload: dict[str, Any]) -> str:
    content = response_payload.get("content")
    if not isinstance(content, list):
        raise PlaceImageExtractionResponseInvalidException()
    text_parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
    text = "".join(text_parts).strip()
    if not text:
        raise PlaceImageExtractionResponseInvalidException()
    return text


async def _call_anthropic(*, image_bytes: bytes, content_type: str) -> list[ExtractedPlaceResponse]:
    api_key = settings.anthropic_api_key
    model = settings.anthropic_image_extraction_model
    if not _is_configured(api_key) or not _is_configured(model):
        raise PlaceImageExtractionServiceUnavailableException()
    _ensure_image_size(image_bytes)

    request_payload = {
        "model": model,
        "max_tokens": settings.anthropic_max_tokens,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content_type,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        },
                    },
                    {"type": "text", "text": _build_prompt(include_schema=True)},
                ],
            }
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": settings.anthropic_api_version,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.anthropic_request_timeout_seconds) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=request_payload)
    except (httpx.TimeoutException, httpx.HTTPError) as exc:
        raise PlaceImageExtractionServiceUnavailableException() from exc

    if response.status_code >= 500:
        raise PlaceImageExtractionServiceUnavailableException()
    if response.status_code >= 400:
        raise PlaceImageExtractionResponseInvalidException()

    try:
        response_payload = response.json()
        ai_payload = _load_json_object(_extract_anthropic_text(response_payload))
        return _parse_ai_payload(ai_payload)
    except (TypeError, ValueError) as exc:
        raise PlaceImageExtractionResponseInvalidException() from exc


async def extract_places_from_image_with_ai(
    *,
    image_bytes: bytes,
    content_type: str,
) -> list[ExtractedPlaceResponse]:
    provider = _selected_provider()
    if provider == ImageExtractionAiProvider.GEMINI:
        return await _call_gemini(image_bytes=image_bytes, content_type=content_type)
    if provider == ImageExtractionAiProvider.OPENAI:
        return await _call_openai(image_bytes=image_bytes, content_type=content_type)
    if provider == ImageExtractionAiProvider.ANTHROPIC:
        return await _call_anthropic(image_bytes=image_bytes, content_type=content_type)
    raise PlaceImageExtractionServiceUnavailableException()
