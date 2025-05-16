
import os
import subprocess
import tempfile
import uuid
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def concatenate_pdfs(request):
    """
    API endpoint to concatenate multiple PDF files into a single PDF.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=400)

    # Check if files were provided
    if 'files' not in request.FILES or not request.FILES.getlist('files'):
        return JsonResponse({'error': 'No PDF files provided'}, status=400)

    files = request.FILES.getlist('files')
    
    # Validate that all files are PDFs
    for file in files:
        if not file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': f'File {file.name} is not a PDF'}, status=400)
    
    # Create a unique directory for this request to avoid file name collisions
    request_id = str(uuid.uuid4())
    temp_dir = os.path.join(settings.TEMP_DIR, request_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save uploaded files to temporary location
    temp_file_paths = []
    output_path = os.path.join(temp_dir, 'concatenated.pdf')
    try:
        for file in files:
            temp_file_path = os.path.join(temp_dir, file.name)
            with open(temp_file_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            temp_file_paths.append(temp_file_path)
        
        # Construct the pdfunite command
        command = ['pdfunite'] + temp_file_paths + [output_path]
        
        # Execute the command
        process = subprocess.run(command, capture_output=True, text=True)
        
        # Check if the command was successful
        if process.returncode != 0:
            return JsonResponse({
                'error': f'Error concatenating PDFs: {process.stderr}'
            }, status=500)
        
        # Return the concatenated PDF
        with open(output_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="concatenated.pdf"'
            return response
            
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    finally:
        # Clean up temporary files
        for path in temp_file_paths:
            if os.path.exists(path):
                os.unlink(path)
        
        # Clean up output file
        if os.path.exists(output_path):
            os.unlink(output_path)
            
        # Remove temporary directory
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)