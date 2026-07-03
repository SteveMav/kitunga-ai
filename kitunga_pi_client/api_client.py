from __future__ import annotations

import logging
from urllib.parse import urlparse

import requests

from config import API_BASE_URL, API_TIMEOUT_SECONDS, BASKET_CODE, DEVICE_ID

logger = logging.getLogger(__name__)


def api_url(api_base_url: str, path: str) -> str:
    parsed = urlparse(path)
    if parsed.scheme and parsed.netloc:
        return path
    return f"{api_base_url.rstrip('/')}/{path.lstrip('/')}"


def detection_url(api_base_url: str = API_BASE_URL, basket_code: str = BASKET_CODE) -> str:
    return api_url(api_base_url, f"/api/baskets/{basket_code}/add-detection/")


def _request_json(method: str, url: str, *, timeout: float, **kwargs) -> dict | None:
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Network/API error for %s %s: %s", method, url, exc)
        return None

    try:
        return response.json()
    except ValueError:
        logger.warning("Backend returned a non-JSON response for %s.", url)
        return None


def start_basket(
    *,
    api_base_url: str = API_BASE_URL,
    device_id: str = DEVICE_ID,
    timeout: float = API_TIMEOUT_SECONDS,
) -> dict | None:
    return _request_json(
        "POST",
        api_url(api_base_url, "/api/baskets/start/"),
        timeout=timeout,
        json={"device_id": device_id},
    )


def get_basket(
    basket_code: str = BASKET_CODE,
    *,
    api_base_url: str = API_BASE_URL,
    timeout: float = API_TIMEOUT_SECONDS,
) -> dict | None:
    return _request_json(
        "GET",
        api_url(api_base_url, f"/api/baskets/{basket_code}/"),
        timeout=timeout,
    )


def finish_basket(
    basket_code: str = BASKET_CODE,
    *,
    api_base_url: str = API_BASE_URL,
    timeout: float = API_TIMEOUT_SECONDS,
) -> dict | None:
    return _request_json(
        "POST",
        api_url(api_base_url, f"/api/baskets/{basket_code}/finish/"),
        timeout=timeout,
        json={},
    )


def send_detection(
    label: str,
    confidence: float,
    *,
    api_base_url: str = API_BASE_URL,
    basket_code: str = BASKET_CODE,
    device_id: str = DEVICE_ID,
    timeout: float = API_TIMEOUT_SECONDS,
) -> dict | None:
    payload = {
        "device_id": device_id,
        "detected_label": label,
        "confidence": round(float(confidence), 2),
    }

    url = detection_url(api_base_url=api_base_url, basket_code=basket_code)
    data = _request_json("POST", url, timeout=timeout, json=payload)
    if data is None:
        return None

    logger.info(
        "Backend response: status=%s message=%s",
        data.get("detection_status", "unknown"),
        data.get("message", "OK"),
    )
    return data
