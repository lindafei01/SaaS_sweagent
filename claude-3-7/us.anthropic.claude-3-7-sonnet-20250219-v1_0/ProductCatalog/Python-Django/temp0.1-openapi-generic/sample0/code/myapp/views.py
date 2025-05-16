
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import Product

@csrf_exempt
@require_http_methods(["POST"])
def add_product(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'name' not in data:
            return JsonResponse({'error': 'Name is required'}, status=400)
        
        name = data.pop('name')
        
        # Check if product with this name already exists
        if Product.objects.filter(name=name).exists():
            return JsonResponse({'error': f'Product with name {name} already exists'}, status=400)
        
        # Create new product
        product = Product(name=name)
        product.set_properties(data)
        product.save()
        
        return JsonResponse({'message': 'Product successfully added'}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
def search_products(request):
    try:
        query = request.GET.get('query', '')
        if not query:
            return JsonResponse({'error': 'Query parameter is required'}, status=400)
        
        # Search in name and properties
        products = Product.objects.all()
        results = []
        
        for product in products:
            product_dict = product.to_dict()
            # Check if query is in name or any property value
            if any(query.lower() in str(value).lower() for value in product_dict.values()):
                results.append(product_dict)
        
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_http_methods(["GET"])
def download_product(request):
    try:
        name = request.GET.get('name')
        if not name:
            return JsonResponse({'error': 'Name parameter is required'}, status=400)
        
        try:
            product = Product.objects.get(name=name)
            return JsonResponse({'data': product.properties})
        except Product.DoesNotExist:
            return JsonResponse({'error': f'Product with name {name} not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def upload_product(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'name' not in data or 'data' not in data:
            return JsonResponse({'error': 'Name and data are required'}, status=400)
        
        name = data['name']
        product_data = data['data']
        
        # Try to parse the data as JSON
        try:
            if isinstance(product_data, str):
                product_properties = json.loads(product_data)
            else:
                product_properties = product_data
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid data format'}, status=400)
        
        # Get or create product
        try:
            product = Product.objects.get(name=name)
        except Product.DoesNotExist:
            return JsonResponse({'error': f'Product with name {name} not found'}, status=404)
        
        # Update product properties
        product.properties = json.dumps(product_properties)
        product.save()
        
        return JsonResponse({'message': f'Product {name} updated successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)