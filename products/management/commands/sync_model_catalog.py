from django.core.management.base import BaseCommand

from detections.label_catalog import LEGACY_LABEL_RENAMES, MODEL_LABELS, product_defaults_for_model_label
from products.models import Product


class Command(BaseCommand):
    help = "Create or update Product rows so the database matches the YOLO model labels."

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

        for model_label in MODEL_LABELS:
            defaults = product_defaults_for_model_label(model_label)
            detection_label = defaults.pop("detection_label")
            _, was_created = Product.objects.update_or_create(
                detection_label=detection_label,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Model catalog synced: {created} created, {updated} updated, {renamed} renamed."
            )
        )
