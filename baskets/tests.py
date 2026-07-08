from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from baskets.models import BasketSession
from checkout.services import validate_checkout
from detections.models import DetectionEvent
from products.models import Product


class BasketApiFlowTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Arduino Uno",
            category="Microcontroleur",
            detection_label="arduino_uno",
            price=Decimal("15.00"),
            currency="USD",
            stock_quantity=10,
        )
        self.servo = Product.objects.create(
            name="Servo moteur SG90",
            category="Actionneur",
            detection_label="servo_sg90",
            price=Decimal("5.00"),
            currency="USD",
            stock_quantity=8,
        )

    def test_ensure_active_creates_then_reuses_active_basket_for_device(self):
        first_response = self.client.post(
            reverse("basket_api:ensure_active"),
            {"device_id": "KITUNGA-PI-001"},
            content_type="application/json",
        )
        second_response = self.client.post(
            reverse("basket_api:ensure_active"),
            {"device_id": "KITUNGA-PI-001"},
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response.json()["code"], second_response.json()["code"])

    def test_detection_adds_product_and_recalculates_total(self):
        start_response = self.client.post(
            reverse("basket_api:start"),
            {"device_id": "KITUNGA-PI-001"},
            content_type="application/json",
        )
        self.assertEqual(start_response.status_code, 201)
        code = start_response.json()["code"]

        detection_response = self.client.post(
            reverse("basket_api:add_detection", kwargs={"code": code}),
            {
                "device_id": "KITUNGA-PI-001",
                "detected_label": "arduino_uno",
                "confidence": "0.91",
            },
            content_type="application/json",
        )

        self.assertEqual(detection_response.status_code, 201)
        body = detection_response.json()
        self.assertEqual(body["detection_status"], DetectionEvent.Status.ACCEPTED)
        self.assertEqual(body["basket"]["total_amount"], "15.00")
        self.assertEqual(body["basket"]["items"][0]["quantity"], 1)

    def test_detection_accepts_raspberry_servo_label(self):
        basket = BasketSession.objects.create(code="SB-PI", device_id="KITUNGA-PI-001")

        response = self.client.post(
            reverse("basket_api:add_detection", kwargs={"code": basket.code}),
            {
                "device_id": "KITUNGA-PI-001",
                "detected_label": "servo_sg90",
                "confidence": "0.90",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["detection_status"], DetectionEvent.Status.ACCEPTED)
        self.assertEqual(body["basket"]["total_amount"], "5.00")
        self.assertEqual(body["basket"]["items"][0]["product_name"], "Servo moteur SG90")

    def test_low_confidence_detection_is_not_added(self):
        basket = BasketSession.objects.create(code="SB-001", device_id="KITUNGA-PI-001")

        response = self.client.post(
            reverse("basket_api:add_detection", kwargs={"code": basket.code}),
            {
                "device_id": "KITUNGA-PI-001",
                "detected_label": "arduino_uno",
                "confidence": "0.50",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["detection_status"], DetectionEvent.Status.LOW_CONFIDENCE)
        basket.refresh_from_db()
        self.assertEqual(basket.items.count(), 0)
        self.assertEqual(basket.total_amount, Decimal("0.00"))

    def test_checkout_validation_marks_paid_and_decrements_stock(self):
        basket = BasketSession.objects.create(code="SB-001", device_id="KITUNGA-PI-001")
        self.client.post(
            reverse("basket_api:add_detection", kwargs={"code": basket.code}),
            {
                "device_id": "KITUNGA-PI-001",
                "detected_label": "arduino_uno",
                "confidence": "0.91",
            },
            content_type="application/json",
        )
        finish_response = self.client.post(reverse("basket_api:finish", kwargs={"code": basket.code}))
        self.assertEqual(finish_response.status_code, 200)

        basket.refresh_from_db()
        transaction = validate_checkout(token=basket.checkout_token, validated_by="tester")

        basket.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal("15.00"))
        self.assertEqual(basket.status, BasketSession.Status.PAID)
        self.assertEqual(self.product.stock_quantity, 9)

    @override_settings(PUBLIC_BASE_URL="http://10.20.20.174:8000")
    def test_finish_generates_public_large_qr_code(self):
        basket = BasketSession.objects.create(code="SB-QR", device_id="KITUNGA-PI-001")
        self.client.post(
            reverse("basket_api:add_detection", kwargs={"code": basket.code}),
            {
                "device_id": "KITUNGA-PI-001",
                "detected_label": "arduino_uno",
                "confidence": "0.91",
            },
            content_type="application/json",
        )

        response = self.client.post(reverse("basket_api:finish", kwargs={"code": basket.code}))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["checkout_url"].startswith("http://10.20.20.174:8000/checkout/t/"))

        qr_path = Path(settings.MEDIA_ROOT) / urlparse(payload["qr_code_url"]).path.removeprefix(settings.MEDIA_URL)
        self.assertTrue(qr_path.exists())
        with Image.open(qr_path) as image:
            self.assertEqual(image.width, image.height)
            self.assertGreaterEqual(image.width, 400)
        qr_path.unlink(missing_ok=True)
