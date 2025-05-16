
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Service

@csrf_exempt
@require_http_methods(["POST"])
def heartbeat(request):
    """
    Register a heartbeat for a service.
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'serviceId' not in data or 'token' not in data:
            return JsonResponse({'error': 'serviceId and token are required'}, status=400)
        
        service_id = data['serviceId']
        token = data['token']
        
        # Find or create service
        service, created = Service.objects.update_or_create(
            service_id=service_id,
            defaults={'token': token, 'last_notification': timezone.now()}
        )
        
        return JsonResponse({'status': 'success'}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def services(request):
    """
    Get overview of registered services.
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if 'token' not in data:
            return JsonResponse({'error': 'token is required'}, status=400)
        
        token = data['token']
        
        # Get all services with matching token
        services_list = Service.objects.filter(token=token)
        
        # Format response
        response_data = []
        for service in services_list:
            response_data.append({
                'serviceId': service.service_id,
                'lastNotification': service.last_notification.isoformat()
            })
        
        return JsonResponse(response_data, safe=False)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)