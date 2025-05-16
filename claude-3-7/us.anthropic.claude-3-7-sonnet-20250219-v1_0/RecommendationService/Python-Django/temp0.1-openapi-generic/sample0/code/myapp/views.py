
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.template.loader import render_to_string
from .models import Product, Tag

@csrf_exempt
@require_http_methods(["GET", "POST"])
def recommender(request):
    """
    Handle GET and POST requests for the recommender endpoint.
    GET: Return products matching the provided tags
    POST: Create a new product with associated tags
    """
    if request.method == 'GET':
        # Get tags from query parameters
        tags_param = request.GET.get('tags', '')
        if not tags_param:
            return HttpResponse("No tags provided", status=400)
        
        # Split the tags by comma
        tag_names = [tag.strip() for tag in tags_param.split(',')]
        
        # Find products that match at least one of the provided tags
        matching_products = Product.objects.filter(tags__name__in=tag_names).distinct()
        
        # Create HTML response
        context = {
            'products': matching_products,
            'tags': tag_names
        }
        
        html_content = render_to_string('myapp/product_list.html', context)
        return HttpResponse(html_content)
    
    elif request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Validate required fields
            if 'product_name' not in data or 'tags' not in data:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            product_name = data['product_name']
            tag_names = data['tags']
            
            # Create new product
            product = Product.objects.create(name=product_name)
            
            # Associate tags with the product
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                tag.products.add(product)
            
            return JsonResponse({'success': True, 'message': 'Product created successfully'})
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)