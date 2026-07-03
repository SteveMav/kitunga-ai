from decimal import Decimal

from django.core.management.base import BaseCommand

from detections.label_catalog import LEGACY_LABEL_RENAMES
from products.models import Product


DEMO_PRODUCTS = [
    {
        "name": "Arduino Uno",
        "category": "Microcontroleur",
        "detection_label": "arduino_uno",
        "price": Decimal("15.00"),
        "currency": "USD",
        "stock_quantity": 10,
    },
    {
        "name": "ESP32 DevKit",
        "category": "Microcontroleur",
        "detection_label": "esp32",
        "price": Decimal("9.50"),
        "currency": "USD",
        "stock_quantity": 14,
    },
    {
        "name": "Capteur ultrason HC-SR04",
        "category": "Capteur",
        "detection_label": "sonar_sensor",
        "price": Decimal("3.00"),
        "currency": "USD",
        "stock_quantity": 18,
    },
    {
        "name": "Breadboard 830 points",
        "category": "Prototypage",
        "detection_label": "breadboard",
        "price": Decimal("4.00"),
        "currency": "USD",
        "stock_quantity": 12,
    },
    {
        "name": "Servo moteur SG90",
        "category": "Actionneur",
        "detection_label": "servo_motor",
        "price": Decimal("5.00"),
        "currency": "USD",
        "stock_quantity": 8,
    },
    {
        "name": "Module relais 1 canal",
        "category": "Module",
        "detection_label": "relay_module",
        "price": Decimal("2.75"),
        "currency": "USD",
        "stock_quantity": 6,
    },
    {
        "name": "Jeu de cables Dupont",
        "category": "Connectique",
        "detection_label": "dupont_wires",
        "price": Decimal("2.00"),
        "currency": "USD",
        "stock_quantity": 20,
    },
]


class Command(BaseCommand):
    help = "Seed demo Fab Lab products for Kitunga AI."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        renamed = 0

        for old_label, new_label in LEGACY_LABEL_RENAMES.items():
            product = Product.objects.filter(detection_label=old_label).first()
            if product and not Product.objects.filter(detection_label=new_label).exists():
                product.detection_label = new_label
                product.save(update_fields=["detection_label"])
                renamed += 1

        for product in DEMO_PRODUCTS:
            _, was_created = Product.objects.update_or_create(
                detection_label=product["detection_label"],
                defaults=product,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {created} created, {updated} updated, {renamed} renamed."
            )
        )
