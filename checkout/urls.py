from django.urls import path

from . import views

app_name = "checkout"

urlpatterns = [
    path("t/<str:token>/", views.checkout_detail, name="checkout_detail"),
    path("t/<str:token>/validate/", views.validate_checkout_view, name="validate"),
]
