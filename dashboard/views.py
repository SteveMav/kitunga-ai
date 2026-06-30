from django.db.models import Count, Sum
from django.shortcuts import render

from baskets.models import BasketSession
from checkout.models import Transaction
from detections.models import DetectionEvent
from products.models import Product


def dashboard_home(request):
    products = Product.objects.all()
    baskets = BasketSession.objects.all()
    transactions = Transaction.objects.select_related("basket")

    context = {
        "product_count": products.count(),
        "basket_count": baskets.count(),
        "pending_count": baskets.filter(status=BasketSession.Status.PENDING_CHECKOUT).count(),
        "paid_count": transactions.filter(status=Transaction.Status.PAID).count(),
        "low_stock_products": products.filter(is_active=True, stock_quantity__lte=3).order_by("stock_quantity", "name")[:8],
        "recent_baskets": baskets.prefetch_related("items").order_by("-created_at")[:8],
        "recent_transactions": transactions.order_by("-created_at")[:8],
        "recent_detections": DetectionEvent.objects.values("status").annotate(count=Count("id")).order_by("status"),
        "total_revenue": transactions.filter(status=Transaction.Status.PAID).aggregate(total=Sum("amount"))["total"] or 0,
    }
    return render(request, "dashboard.html", context)
