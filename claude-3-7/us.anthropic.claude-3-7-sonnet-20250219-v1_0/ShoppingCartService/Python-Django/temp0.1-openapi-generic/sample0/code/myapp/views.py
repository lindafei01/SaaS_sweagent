
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError, transaction
from .models import Cart, CartItem

@csrf_exempt
@require_http_methods(["POST"])
def create_cart(request):
    """Create a new shopping cart."""
    try:
        cart = Cart.objects.create()
        return JsonResponse({"cart_id": str(cart.cart_id)}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_to_cart(request):
    """Add or remove items from the cart."""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['cart_id', 'item_id', 'count']
        for field in required_fields:
            if field not in data:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)
        
        cart_id = data['cart_id']
        item_id = data['item_id']
        count = data['count']
        
        # Validate data types
        if not isinstance(item_id, int):
            return JsonResponse({"error": "item_id must be an integer"}, status=400)
        if not isinstance(count, int):
            return JsonResponse({"error": "count must be an integer"}, status=400)
        
        try:
            cart = Cart.objects.get(cart_id=cart_id)
        except Cart.DoesNotExist:
            return JsonResponse({"error": "Cart not found"}, status=404)
        
        with transaction.atomic():
            try:
                # Try to get the existing cart item
                cart_item = CartItem.objects.get(cart=cart, item_id=item_id)
                
                # Update the count
                cart_item.count += count
                
                # If count is zero or negative, remove the item
                if cart_item.count <= 0:
                    cart_item.delete()
                else:
                    cart_item.save()
                    
            except CartItem.DoesNotExist:
                # If the item doesn't exist and count is positive, create it
                if count > 0:
                    CartItem.objects.create(cart=cart, item_id=item_id, count=count)
                else:
                    # If trying to remove an item that doesn't exist, just ignore
                    pass
        
        return JsonResponse({"message": "Item updated successfully"}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def retrieve_cart(request):
    """Retrieve all items in the cart."""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'cart_id' not in data:
            return JsonResponse({"error": "Missing required field: cart_id"}, status=400)
        
        cart_id = data['cart_id']
        
        try:
            cart = Cart.objects.get(cart_id=cart_id)
        except Cart.DoesNotExist:
            return JsonResponse({"error": "Cart not found"}, status=404)
        
        # Get all items in the cart
        items = cart.items.all().values('item_id', 'count')
        
        return JsonResponse({"items": list(items)}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)