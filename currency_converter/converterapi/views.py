from django.shortcuts import render
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class CurrencyConverterAPIView(APIView):
    """
    API view to convert currency from one to another using an external API live exchange rates.
    """
    def get(self, request):
        base_currency = request.query_params.get('base', 'USD')
        target_currency = request.query_params.get('target', 'NGN')
        amount = request.query_params.get('amount', 1)

        # validate presence of parameters
        if not all([base_currency, target_currency, amount]):
            return Response({"error": "Missing required query parameters."}, status=status.HTTP_400_BAD_REQUEST)

        # validate base currency
        if not base_currency.isalpha() or len(base_currency) != 3:
            return Response({"error": "Invalid base currency code"}, status=status.HTTP_400_BAD_REQUEST)

        # validate target currency
        if not target_currency.isalpha() or len(target_currency) != 3:
            return Response({"error": "Invalid target currency code"}, status=status.HTTP_400_BAD_REQUEST)
        
        # validate that base and target currencies are not the same
        if base_currency.upper() == target_currency.upper():
            return Response({"error": "Base and target currencies must be different"}, status=status.HTTP_400_BAD_REQUEST)
        
        # validate that currencies are in uppercase
        base_currency = base_currency.upper()
        target_currency = target_currency.upper()

        # validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                return Response({"error": "Amount must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Amount must be a number"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Call the external API to get exchange rates
        api_key = settings.EXCHANGE_API_KEY
        url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}'

        # Make the request to the external API
        data = {}  # initialize data to avoid reference before assignment error
        try:
            response = requests.get(url)
            print(response)

            # if base currency not supported, use USD as fallback
            if response.status_code != 200 or data.get('result') != 'success':
                # Retry using USD as base currency
                fallback_url = f'https://v6.exchangerate-api.com/v6/{api_key}/latest/USD'
                response = requests.get(fallback_url)
                data = response.json()

                if data.get('result') != 'success':
                    return Response({"error": "Failed to fetch exchange rates."}, status=status.HTTP_502_BAD_GATEWAY)
                rates = data.get('conversion_rates', {})
                if base_currency not in rates or target_currency not in rates:
                    return Response({"error": f"Invalid or Unsupported currency codes."}, status=status.HTTP_400_BAD_REQUEST)
            
                # Compute using USD as bridge
                usd_to_base = rates[base_currency]
                usd_to_target = rates[target_currency]
                rate = usd_to_target / usd_to_base  # base to target rate
            else:
                # if base currency is supported directly
                rates = data.get('conversion_rates', {})
                print(rates)
                if target_currency not in rates:
                    return Response({"error": f"Invalid or Unsupported target currency: {target_currency}"}, status=status.HTTP_400_BAD_REQUEST)
                rate = rates[target_currency]
        
            data = response.json()
            print(data)
            if data.get('result') != 'success':
                return Response({"error": data.get('error-type', "Unknown error occurred.")}, status=status.HTTP_502_BAD_GATEWAY)
            
            rate = round(rate, 5)
            converted_amount = amount * rate
            converted_amount = round(converted_amount, 2)
        
            # Extract the returned data
            result = {
                'base': base_currency,
                'target': target_currency,
                'amount': amount,
                'rate': rate,
                'converted_amount': converted_amount
            }

            # Return the converted result
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)