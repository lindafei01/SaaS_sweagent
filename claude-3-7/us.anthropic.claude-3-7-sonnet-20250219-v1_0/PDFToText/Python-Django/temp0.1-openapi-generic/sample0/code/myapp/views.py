
import os
import subprocess
import tempfile
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def convert_pdf_to_text(request):
    """
    Convert a PDF file to text using pdftotext utility
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=400)
    
    # Check if file is provided
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    pdf_file = request.FILES['file']
    
    # Check if file is a PDF
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'File must be a PDF'}, status=400)
    
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name
        
        # Create a temporary file for the output text
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_txt:
            temp_txt_path = temp_txt.name
        
        # Run pdftotext command
        try:
            subprocess.run(['pdftotext', temp_pdf_path, temp_txt_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error converting PDF to text: {e}")
            return JsonResponse({'error': 'Failed to convert PDF to text'}, status=500)
        
        # Read the text content
        with open(temp_txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Clean up temporary files
        os.unlink(temp_pdf_path)
        os.unlink(temp_txt_path)
        
        # Return the text content
        response = HttpResponse(text_content, content_type='text/plain')
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)