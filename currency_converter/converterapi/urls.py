from django.urls import path
from .views import CurrencyConverterAPIView

# URL patterns for the converterapi app
urlpatterns = [
    path('convert/', CurrencyConverterAPIView.as_view(), name='currency-convert'),
]