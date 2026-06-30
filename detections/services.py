from decimal import Decimal

from baskets.services import CONFIDENCE_THRESHOLD


def is_confident_enough(confidence: Decimal) -> bool:
    return confidence >= CONFIDENCE_THRESHOLD
