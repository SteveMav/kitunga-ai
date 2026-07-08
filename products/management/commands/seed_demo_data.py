from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import Product

DEMO_LABEL_RENAMES = {
    "breadboard": "breadboard_830",
    "esp32": "esp32_devkit",
    "relay_module": "relay_module_1ch",
    "servo_motor": "servo_sg90",
    "sonar_sensor": "hc_sr04",
}


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
        "detection_label": "esp32_devkit",
        "price": Decimal("9.50"),
        "currency": "USD",
        "stock_quantity": 14,
    },
    {
        "name": "Capteur ultrason HC-SR04",
        "category": "Capteur",
        "detection_label": "hc_sr04",
        "price": Decimal("3.00"),
        "currency": "USD",
        "stock_quantity": 18,
    },
    {
        "name": "Breadboard 830 points",
        "category": "Prototypage",
        "detection_label": "breadboard_830",
        "price": Decimal("4.00"),
        "currency": "USD",
        "stock_quantity": 12,
    },
    {
        "name": "Servo moteur SG90",
        "category": "Actionneur",
        "detection_label": "servo_sg90",
        "price": Decimal("5.00"),
        "currency": "USD",
        "stock_quantity": 8,
    },
    {
        "name": "Module relais 1 canal",
        "category": "Module",
        "detection_label": "relay_module_1ch",
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

        for current_label, target_label in DEMO_LABEL_RENAMES.items():
            product = Product.objects.filter(detection_label=current_label).first()
            target_exists = Product.objects.filter(detection_label=target_label).exists()
            if product and not target_exists:
                product.detection_label = target_label
                product.save(update_fields=["detection_label"])
                renamed += 1
            elif product and target_exists and product.is_active:
                product.is_active = False
                product.save(update_fields=["is_active"])

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
