
import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import Message

def index_view(request):
    """Simple view to render the index page or redirect to messages."""
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["GET", "POST"])
def messages_view(request):
    if request.method == 'GET':
        # Get query parameters with defaults
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        sort = request.GET.get('sort', 'DESC').upper()
        
        # Get messages with proper sorting
        if sort == 'ASC':
            messages = Message.objects.all().order_by('created_at')
        else:  # Default to DESC
            messages = Message.objects.all().order_by('-created_at')
        
        # Apply pagination
        paginator = Paginator(messages, limit)
        page_number = (offset // limit) + 1
        page_obj = paginator.get_page(page_number)
        
        # Prepare messages for display
        messages_list = []
        for message in page_obj:
            messages_list.append({
                'username': message.username,
                'content': message.content,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Render HTML response
        return render(request, 'messages.html', {
            'messages': messages_list,
            'limit': limit,
            'offset': offset,
            'sort': sort,
        })
    
    elif request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            
            # Validate required fields
            if 'content' not in data or 'username' not in data:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            # Create new message
            message = Message.objects.create(
                content=data['content'],
                username=data['username']
            )
            
            return JsonResponse({'status': 'success'}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)