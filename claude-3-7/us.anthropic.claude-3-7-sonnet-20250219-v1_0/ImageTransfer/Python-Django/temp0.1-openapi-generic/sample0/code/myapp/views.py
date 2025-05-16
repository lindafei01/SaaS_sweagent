
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from .models import Image
import json

@csrf_exempt
def upload_image(request):
    """
    Handle image upload and return a shareable link
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=400)
    
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    file = request.FILES['file']
    
    # Check if the file is an image
    content_type = file.content_type
    if not content_type.startswith('image/'):
        return JsonResponse({'error': 'File must be an image'}, status=400)
    
    try:
        # Create a new image record
        image = Image.objects.create(
            file=file,
            content_type=content_type
        )
        
        return JsonResponse({'id': str(image.id)}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_image(request, imageId):
    """
    Retrieve and display an image by its ID
    """
    try:
        # Try to get the image by ID
        from django.http import Http404
        from uuid import UUID
        
        try:
            # Validate UUID format
            uuid_obj = UUID(imageId, version=4)
        except ValueError:
            raise Http404("Invalid image ID format")
            
        try:
            image = Image.objects.get(id=imageId)
        except Image.DoesNotExist:
            raise Http404("Image not found")
        
        # Return the image with its original content type
        response = FileResponse(image.file.open('rb'), content_type=image.content_type)
        
        # Set headers to display in browser rather than download
        response['Content-Disposition'] = f'inline; filename="{image.file.name}"'
        
        return response
    except Http404 as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)