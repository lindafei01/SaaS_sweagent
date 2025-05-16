
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .models import CreditCard, PhoneNumber

@csrf_exempt
@require_http_methods(["POST"])
def associate_card(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'credit_card' not in data or 'phone' not in data:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        credit_card_number = data['credit_card']
        phone_number = data['phone']
        
        # Validate input data
        if not credit_card_number or not phone_number:
            return JsonResponse({'error': 'Invalid input data'}, status=400)
        
        with transaction.atomic():
            # Get or create credit card
            credit_card, _ = CreditCard.objects.get_or_create(card_number=credit_card_number)
            
            # Get or create phone number
            phone, _ = PhoneNumber.objects.get_or_create(phone_number=phone_number)
            
            # Associate credit card with phone number
            phone.credit_cards.add(credit_card)
        
        return JsonResponse({}, status=201)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def retrieve_cards(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'phone_numbers' not in data:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        phone_numbers = data['phone_numbers']
        
        # Validate input data
        if not isinstance(phone_numbers, list) or not phone_numbers:
            return JsonResponse({'error': 'Invalid phone_numbers format'}, status=400)
        
        # Find all credit cards associated with the first phone number
        try:
            first_phone = PhoneNumber.objects.get(phone_number=phone_numbers[0])
            card_set = set(first_phone.credit_cards.values_list('card_number', flat=True))
            
            # For each additional phone number, find the intersection of card sets
            for phone_number in phone_numbers[1:]:
                try:
                    phone = PhoneNumber.objects.get(phone_number=phone_number)
                    phone_cards = set(phone.credit_cards.values_list('card_number', flat=True))
                    card_set = card_set.intersection(phone_cards)
                except PhoneNumber.DoesNotExist:
                    # If any phone number doesn't exist, return empty set
                    card_set = set()
                    break
                    
            # Convert set to list for JSON serialization
            card_numbers = list(card_set)
            
            if not card_numbers:
                return JsonResponse({'error': 'No matching credit cards found'}, status=404)
                
            return JsonResponse({'card_numbers': card_numbers}, status=200)
            
        except PhoneNumber.DoesNotExist:
            return JsonResponse({'error': 'No matching credit cards found'}, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)