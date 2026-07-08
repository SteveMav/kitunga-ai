from django.urls import path

from . import views

app_name = "basket_api"

urlpatterns = [
    path("start/", views.start_basket, name="start"),
    path("ensure-active/", views.ensure_active_basket, name="ensure_active"),
    path("<str:code>/", views.basket_detail, name="detail"),
    path("<str:code>/add-detection/", views.add_detection, name="add_detection"),
    path("<str:code>/remove-item/", views.remove_item, name="remove_item"),
    path("<str:code>/finish/", views.finish_basket_api, name="finish"),
]
