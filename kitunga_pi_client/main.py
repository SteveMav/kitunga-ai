from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from api_client import send_detection
from camera import capture_image
from config import (
    API_BASE_URL,
    BASKET_CODE,
    CAMERA_INDEX,
    CONFIDENCE_THRESHOLD,
    COOLDOWN_SECONDS,
    DEVICE_ID,
    MODEL_PATH,
    SCAN_INTERVAL_SECONDS,
    TEST_IMAGE_PATH,
)
from detector import YoloObjectDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kitunga AI Raspberry Pi detection client")
    parser.add_argument("--api-base-url", default=API_BASE_URL, help="Django backend base URL")
    parser.add_argument("--basket-code", default=BASKET_CODE, help="Basket session code")
    parser.add_argument("--device-id", default=DEVICE_ID, help="Device identifier")
    parser.add_argument("--camera-index", type=int, default=CAMERA_INDEX, help="OpenCV camera index")
    parser.add_argument("--model-path", default=str(MODEL_PATH), help="YOLO model path")
    parser.add_argument("--test-image", default=TEST_IMAGE_PATH, help="Use a fixed image instead of the camera")
    parser.add_argument("--threshold", type=float, default=CONFIDENCE_THRESHOLD, help="Minimum confidence to send")
    parser.add_argument("--cooldown", type=float, default=COOLDOWN_SECONDS, help="Duplicate cooldown per label")
    parser.add_argument("--interval", type=float, default=SCAN_INTERVAL_SECONDS, help="Seconds between scans")
    parser.add_argument("--once", action="store_true", help="Run one capture/detection cycle then exit")
    parser.add_argument("--no-send", action="store_true", help="Detect only, do not call the backend")
    return parser.parse_args()


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def should_skip_duplicate(label: str, last_sent_at: dict[str, float], cooldown: float) -> bool:
    previous = last_sent_at.get(label)
    return previous is not None and (time.monotonic() - previous) < cooldown


def main() -> None:
    configure_logging()
    args = parse_args()
    logger = logging.getLogger("kitunga_pi_client")
    last_sent_at: dict[str, float] = {}

    logger.info("Kitunga AI client starting")
    logger.info("Backend=%s basket=%s device=%s", args.api_base_url, args.basket_code, args.device_id)
    logger.info("Mode=%s", "test image" if args.test_image else f"camera index {args.camera_index}")

    try:
        detector = YoloObjectDetector(args.model_path)
    except Exception as exc:
        logger.error("Detector initialization failed: %s", exc)
        logger.error("For simulation, place a trained model at %s or pass --model-path.", args.model_path)
        return

    while True:
        try:
            image_path = capture_image(
                camera_index=args.camera_index,
                test_image_path=Path(args.test_image) if args.test_image else None,
            )
            logger.info("Captured image: %s", image_path)

            result = detector.detect(image_path)
            if not result.found:
                logger.info("No object detected.")
            elif result.confidence < args.threshold:
                logger.info(
                    "Ignored low confidence detection: label=%s confidence=%.2f threshold=%.2f",
                    result.label,
                    result.confidence,
                    args.threshold,
                )
            elif should_skip_duplicate(result.label, last_sent_at, args.cooldown):
                logger.info("Skipped duplicate label=%s within %.1fs cooldown.", result.label, args.cooldown)
            else:
                logger.info("Detected label=%s confidence=%.2f", result.label, result.confidence)
                if args.no_send:
                    logger.info("No-send mode enabled, backend call skipped.")
                else:
                    response = send_detection(
                        result.label,
                        result.confidence,
                        api_base_url=args.api_base_url,
                        basket_code=args.basket_code,
                        device_id=args.device_id,
                    )
                    if response is not None:
                        last_sent_at[result.label] = time.monotonic()
        except KeyboardInterrupt:
            logger.info("Stopped by user.")
            break
        except Exception as exc:
            logger.exception("Cycle failed, continuing: %s", exc)

        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
