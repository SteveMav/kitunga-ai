from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer


@api_view(["GET"])
def product_list(request):
    products = Product.objects.filter(is_active=True).order_by("category", "name")
    serializer = ProductSerializer(products, many=True, context={"request": request})
    return Response(serializer.data)
