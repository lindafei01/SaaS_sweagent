
import os
import json
import mimetypes
from django.http import HttpResponse, JsonResponse, FileResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_http_methods
import re

@csrf_exempt
@require_http_methods(["POST"])
def download_song(request):
    """
    Endpoint to download a song from the server.
    Accepts a POST request with a JSON body containing the filename.
    Returns the song file as a streaming response.
    """
    try:
        # Parse the JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        
        # Get the filename from the request
        filename = data.get('filename')
        if not filename:
            return JsonResponse({"error": "Filename is required"}, status=400)
        
        # Validate the filename to prevent directory traversal attacks
        if not is_safe_filename(filename):
            return JsonResponse({"error": "Invalid filename"}, status=400)
        
        # Build the full path to the song file
        file_path = os.path.join(settings.SONGS_DIR, filename)
        
        # Check if the file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return JsonResponse({"error": "File not found"}, status=404)
        
        # Determine the content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'audio/mpeg'  # Default to audio/mpeg if type can't be determined
        
        # Create a streaming response
        response = StreamingHttpResponse(
            file_iterator(file_path),
            content_type=content_type
        )
        
        # Set the Content-Disposition header to suggest a filename to the browser
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def file_iterator(file_path, chunk_size=8192):
    """
    Generator function to stream file content in chunks.
    """
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def is_safe_filename(filename):
    """
    Check if the filename is safe (no directory traversal).
    """
    # Check for directory traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Only allow alphanumeric characters, underscores, hyphens, and dots
    if not re.match(r'^[\w\-. ]+$', filename):
        return False
    
    return True