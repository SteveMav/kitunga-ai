from django.urls import path

from . import views

app_name = "baskets"

urlpatterns = [
    path("basket-screen/<str:code>/", views.basket_screen, name="basket_screen"),
]
