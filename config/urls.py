from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("", include("baskets.urls")),
    path("api/products/", include("products.urls")),
    path("api/baskets/", include("baskets.api_urls")),
    path("api/detections/", include("detections.urls")),
    path("checkout/", include("checkout.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
