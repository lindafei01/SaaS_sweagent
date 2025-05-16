
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from .models import Recipe, Comment, Rating

def recipes_overview(request):
    """Get an overview of recipes"""
    recent_recipes = Recipe.objects.order_by('-created_at')[:5]
    
    # Get top rated recipes
    all_recipes = Recipe.objects.all()
    # Sort by average rating (non-null ratings first)
    top_recipes = sorted(
        [r for r in all_recipes if r.avg_rating is not None],
        key=lambda x: x.avg_rating,
        reverse=True
    )[:5]
    
    context = {
        'recent_recipes': recent_recipes,
        'top_recipes': top_recipes
    }
    
    # Return HTML response
    return render(request, 'myapp/recipes_overview.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def upload_recipe(request):
    """Upload a new recipe"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'ingredients', 'instructions']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
        
        # Validate ingredients is a list
        if not isinstance(data['ingredients'], list):
            return JsonResponse({'error': 'Ingredients must be a list'}, status=400)
        
        # Create recipe
        recipe = Recipe.objects.create(
            title=data['title'],
            ingredients=data['ingredients'],
            instructions=data['instructions']
        )
        
        # Return recipe data
        return JsonResponse({
            'id': str(recipe.id),
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions,
            'comments': [],
            'avgRating': None
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_recipe(request, recipe_id):
    """Get a recipe by ID"""
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        
        # Get comments for this recipe
        comments = Comment.objects.filter(recipe=recipe).order_by('-created_at')
        
        context = {
            'recipe': recipe,
            'comments': comments,
            'avg_rating': recipe.avg_rating
        }
        
        # Return HTML response
        return render(request, 'myapp/recipe_detail.html', context)
        
    except Http404:
        return HttpResponse("Recipe not found", status=404)
    except Exception as e:
        return HttpResponse(str(e), status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_comment(request, recipe_id):
    """Add a comment to a recipe"""
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = json.loads(request.body)
        
        # Validate required fields
        if 'comment' not in data:
            return JsonResponse({'error': 'Missing required field: comment'}, status=400)
        
        # Create comment
        comment = Comment.objects.create(
            recipe=recipe,
            comment=data['comment']
        )
        
        return JsonResponse({'success': 'Comment added successfully'}, status=201)
        
    except Http404:
        return JsonResponse({'error': 'Recipe not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_rating(request, recipe_id):
    """Rate a recipe"""
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = json.loads(request.body)
        
        # Validate required fields
        if 'rating' not in data:
            return JsonResponse({'error': 'Missing required field: rating'}, status=400)
        
        # Validate rating value
        rating_value = data['rating']
        if not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
            return JsonResponse({'error': 'Rating must be an integer between 1 and 5'}, status=400)
        
        # Create rating
        rating = Rating.objects.create(
            recipe=recipe,
            rating=rating_value
        )
        
        return JsonResponse({'success': 'Rating added successfully'}, status=201)
        
    except Http404:
        return JsonResponse({'error': 'Recipe not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)