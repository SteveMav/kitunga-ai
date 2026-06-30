from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from baskets.models import BasketSession

from .services import validate_checkout


def _basket_by_token(token: str) -> BasketSession:
    return get_object_or_404(
        BasketSession.objects.prefetch_related("items__product").select_related("transaction"),
        checkout_token=token,
    )


def checkout_detail(request, token: str):
    basket = _basket_by_token(token)
    if basket.status == BasketSession.Status.PAID and hasattr(basket, "transaction"):
        return render(request, "ticket.html", {"basket": basket, "transaction": basket.transaction})
    return render(request, "checkout.html", {"basket": basket})


@require_POST
def validate_checkout_view(request, token: str):
    validated_by = request.POST.get("validated_by") or "demo_cashier"
    if request.user.is_authenticated:
        validated_by = request.user.get_username()

    try:
        transaction = validate_checkout(token=token, validated_by=validated_by)
    except BasketSession.DoesNotExist:
        messages.error(request, "Panier introuvable.")
        return redirect("dashboard:dashboard")
    except DjangoValidationError as error:
        messages.error(request, error.messages[0] if hasattr(error, "messages") else str(error))
        return redirect("checkout:checkout_detail", token=token)

    basket = _basket_by_token(token)
    return render(request, "ticket.html", {"basket": basket, "transaction": transaction})
