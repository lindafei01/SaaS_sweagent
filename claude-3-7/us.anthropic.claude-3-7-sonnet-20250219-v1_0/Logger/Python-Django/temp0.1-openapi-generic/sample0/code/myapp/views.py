
import json
import os
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def log_message(request):
    """
    Log a message to the server.
    Endpoint: /log
    Method: POST
    Request Body: {"message": "This is a log message"}
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Format the log entry with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        # Ensure the log file exists
        os.makedirs(os.path.dirname(settings.LOG_FILE_PATH), exist_ok=True)
        
        # Write to the log file
        with open(settings.LOG_FILE_PATH, 'a') as log_file:
            log_file.write(log_entry)
        
        return JsonResponse({'status': 'success'}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_logs(request):
    """
    Retrieve all logged messages.
    Endpoint: /logs
    Method: GET
    """
    try:
        # Check if log file exists
        if not os.path.exists(settings.LOG_FILE_PATH):
            return HttpResponse('', content_type='text/plain')
        
        # Read the log file
        with open(settings.LOG_FILE_PATH, 'r') as log_file:
            logs = log_file.read()
        
        return HttpResponse(logs, content_type='text/plain')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)