from __future__ import annotations

import logging

import requests

from config import API_BASE_URL, API_TIMEOUT_SECONDS, BASKET_CODE, DEVICE_ID

logger = logging.getLogger(__name__)


def detection_url(api_base_url: str = API_BASE_URL, basket_code: str = BASKET_CODE) -> str:
    return f"{api_base_url.rstrip('/')}/api/baskets/{basket_code}/add-detection/"


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
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Network/API error while sending %s: %s", label, exc)
        return None

    try:
        data = response.json()
    except ValueError:
        logger.warning("Backend returned a non-JSON response for %s.", label)
        return None

    logger.info(
        "Backend response: status=%s message=%s",
        data.get("detection_status", response.status_code),
        data.get("message", "OK"),
    )
    return data
