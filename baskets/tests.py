from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

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
