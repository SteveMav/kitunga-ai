from pathlib import Path
from unittest.mock import patch

from django.test import Client
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from baskets.models import BasketSession
from detections.yolo import YoloDetection
from products.models import Product


class CaptureFrameTests(TestCase):
    def test_csrf_token_endpoint_allows_browser_post_with_token(self):
        client = Client(enforce_csrf_checks=True)
        token_response = client.get(reverse("detections:csrf_token"))
        self.assertEqual(token_response.status_code, 200)

        token = client.cookies["csrftoken"].value
        response = client.post(
            reverse("detections:live_detect_frame"),
            {"device_id": "IRIUN-PC-TEST"},
            HTTP_ORIGIN="http://127.0.0.1:5174",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Champ image requis.")

    def test_capture_frame_saves_uploaded_image(self):
        image = SimpleUploadedFile(
            "frame.jpg",
            b"\xff\xd8\xff\xe0" + b"kitunga-test" + b"\xff\xd9",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("detections:capture_frame"),
            {"device_id": "TEST-CAM", "image": image},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["status"], "saved")
        saved_path = Path(payload["saved_path"])
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.parent, Path(settings.BASE_DIR) / "kitunga_pi_client" / "captures")
        saved_path.unlink(missing_ok=True)

    def test_capture_frame_requires_image(self):
        response = self.client.post(reverse("detections:capture_frame"), {"device_id": "TEST-CAM"})
        self.assertEqual(response.status_code, 400)

    @patch("detections.views.detect_best_label")
    def test_capture_and_detect_adds_detected_product_to_basket(self, mock_detect):
        Product.objects.create(
            name="Servo moteur SG90",
            category="Actionneur",
            detection_label="servo_motor",
            price="5.00",
            currency="USD",
            stock_quantity=8,
        )
        basket = BasketSession.objects.create(code="SB-TEST", device_id="IRIUN-PC-TEST")
        mock_detect.return_value = YoloDetection(label="servo_motor", confidence=0.91)
        image = SimpleUploadedFile(
            "servo.jpg",
            b"\xff\xd8\xff\xe0" + b"kitunga-servo-test" + b"\xff\xd9",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("detections:capture_and_detect"),
            {
                "device_id": "IRIUN-PC-TEST",
                "basket_code": basket.code,
                "image": image,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["detected_label"], "servo_motor")
        self.assertEqual(payload["detection_status"], "accepted")
        self.assertEqual(payload["basket"]["items"][0]["product_name"], "Servo moteur SG90")
        saved_path = Path(payload["capture"]["saved_path"])
        saved_path.unlink(missing_ok=True)

    @patch("detections.views.detect_objects")
    def test_live_detect_frame_returns_detection_boxes(self, mock_detect_objects):
        mock_detect_objects.return_value = [
            YoloDetection(
                label="servo_motor",
                raw_label="Servo-Motor",
                confidence=0.88,
                box={
                    "x1": 0.1,
                    "y1": 0.2,
                    "x2": 0.6,
                    "y2": 0.7,
                    "pixel_x1": 64,
                    "pixel_y1": 96,
                    "pixel_x2": 384,
                    "pixel_y2": 336,
                },
            )
        ]
        image = SimpleUploadedFile(
            "live.jpg",
            b"\xff\xd8\xff\xe0" + b"kitunga-live-test" + b"\xff\xd9",
            content_type="image/jpeg",
        )

        response = self.client.post(
            reverse("detections:live_detect_frame"),
            {
                "device_id": "IRIUN-PC-TEST",
                "min_confidence": "0.25",
                "image": image,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "detected")
        self.assertEqual(payload["detections"][0]["label"], "servo_motor")
        self.assertEqual(payload["detections"][0]["raw_label"], "Servo-Motor")
        self.assertEqual(payload["detections"][0]["box"]["x1"], 0.1)
        Path(payload["capture"]["saved_path"]).unlink(missing_ok=True)
