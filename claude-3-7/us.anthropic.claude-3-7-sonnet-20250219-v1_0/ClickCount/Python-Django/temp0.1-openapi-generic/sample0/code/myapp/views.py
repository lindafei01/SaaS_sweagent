
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_date
from django.utils import timezone
from .models import Click
import json
from datetime import datetime, time

@csrf_exempt
@require_http_methods(["POST"])
def register_click(request):
    """Endpoint to register a user's click in the database."""
    try:
        click = Click.objects.create()
        return JsonResponse({}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@require_http_methods(["GET"])
def retrieve_clicks(request):
    """Endpoint to retrieve clicks before or after a certain date."""
    try:
        date_str = request.GET.get('date')
        direction = request.GET.get('direction')
        
        if not date_str or not direction:
            return JsonResponse({"error": "Both date and direction parameters are required"}, status=400)
        
        # Parse the date
        date = parse_date(date_str)
        if not date:
            return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)
        
        # Convert date to datetime for comparison
        date_time = timezone.make_aware(datetime.combine(date, time.min))
        
        # Validate direction
        valid_directions = ['<', '>', '<=', '>=']
        if direction not in valid_directions:
            return JsonResponse({"error": f"Direction must be one of {', '.join(valid_directions)}"}, status=400)
        
        # Query based on direction
        if direction == '<':
            clicks = Click.objects.filter(timestamp__lt=date_time)
        elif direction == '>':
            clicks = Click.objects.filter(timestamp__gt=date_time)
        elif direction == '<=':
            clicks = Click.objects.filter(timestamp__lte=date_time)
        elif direction == '>=':
            clicks = Click.objects.filter(timestamp__gte=date_time)
        
        if not clicks.exists():
            return JsonResponse({"error": "No clicks found"}, status=404)
        
        # Format the response
        result = []
        for click in clicks:
            result.append({
                "id": str(click.id),
                "timestamp": click.timestamp.isoformat()
            })
        
        return JsonResponse(result, safe=False)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)