
import os
import tempfile
import subprocess
import uuid
import re
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def create_gif(request):
    """
    Create a GIF from uploaded images with specified parameters.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    # Check if images are provided
    if 'images' not in request.FILES:
        return JsonResponse({'error': 'No images provided'}, status=400)
    
    # Check if targetSize is provided
    if 'targetSize' not in request.POST:
        return JsonResponse({'error': 'Target size is required'}, status=400)
    
    # Validate target size format (e.g., 500x500)
    target_size = request.POST.get('targetSize')
    if not re.match(r'^\d+x\d+$', target_size):
        return JsonResponse({'error': 'Invalid target size format. Use WIDTHxHEIGHT (e.g., 500x500)'}, status=400)
    
    # Get delay parameter (default: 10ms)
    try:
        delay = int(request.POST.get('delay', 10))
        if delay <= 0:
            return JsonResponse({'error': 'Delay must be a positive integer'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Delay must be a valid integer'}, status=400)
    
    # Get appendReverted parameter (default: False)
    append_reverted = request.POST.get('appendReverted', 'false').lower() in ['true', '1', 'yes']
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp(dir=settings.TEMP_UPLOAD_DIR)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save uploaded images to temporary directory
    image_paths = []
    try:
        for i, image_file in enumerate(request.FILES.getlist('images')):
            # Generate a unique filename
            ext = os.path.splitext(image_file.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return JsonResponse({'error': f'Unsupported image format: {ext}'}, status=400)
            
            temp_path = os.path.join(temp_dir, f'image_{i}{ext}')
            with open(temp_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            image_paths.append(temp_path)
        
        if not image_paths:
            return JsonResponse({'error': 'No valid images provided'}, status=400)
        
        # Create output GIF path
        output_gif = os.path.join(temp_dir, f'output_{uuid.uuid4()}.gif')
        
        # Prepare ImageMagick command
        convert_cmd = ['convert']
        
        # Add resize parameter
        convert_cmd.extend(['-resize', target_size])
        
        # Add delay parameter (convert from ms to 1/100 of a second)
        delay_cs = max(1, delay // 10)  # Ensure minimum delay of 1/100 sec
        convert_cmd.extend(['-delay', str(delay_cs)])
        
        # Add input images
        convert_cmd.extend(image_paths)
        
        # Add reverted images if requested
        if append_reverted:
            convert_cmd.extend(reversed(image_paths))
        
        # Add output path
        convert_cmd.append(output_gif)
        
        # Execute ImageMagick command
        try:
            subprocess.run(convert_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({
                'error': f'Error creating GIF: {e.stderr.decode() if e.stderr else "Unknown error"}'
            }, status=500)
        
        # Return the GIF
        with open(output_gif, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/gif')
            response['Content-Disposition'] = 'inline; filename="output.gif"'
            return response
            
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
    finally:
        # Clean up temporary files
        for path in image_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        
        if 'output_gif' in locals() and os.path.exists(output_gif):
            try:
                os.remove(output_gif)
            except:
                pass
        
        try:
            os.rmdir(temp_dir)
        except:
            pass