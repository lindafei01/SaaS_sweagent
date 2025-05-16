
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import zipfile
import io

@csrf_exempt
def convert_zip_to_text(request):
    """
    View function to convert a zip file to a text file.
    
    This function:
    1. Receives a zip file from a POST request
    2. Extracts all text files from the zip
    3. Concatenates the contents of all text files
    4. Returns the concatenated text as a response
    """
    if request.method != 'POST':
        return HttpResponse("Only POST method is allowed", status=400)
    
    # Check if file is in request
    if 'file' not in request.FILES:
        return HttpResponse("No file provided", status=400)
    
    uploaded_file = request.FILES['file']
    
    # Try to open the file as a zip file
    try:
        # Read the uploaded file into memory
        file_content = uploaded_file.read()
        zip_file = zipfile.ZipFile(io.BytesIO(file_content))
        
        # Extract and concatenate all text files
        text_content = ""
        for file_info in zip_file.infolist():
            # Skip directories
            if file_info.is_dir():
                continue
            
            # Read file content
            file_content = zip_file.read(file_info.filename)
            
            # Try to decode as text
            try:
                text_content += file_content.decode('utf-8')
            except UnicodeDecodeError:
                # Skip binary files
                continue
        
        # Return the concatenated text
        return HttpResponse(text_content, content_type='text/plain')
    
    except zipfile.BadZipFile:
        return HttpResponse("Invalid zip file", status=400)
    except Exception as e:
        return HttpResponse(f"Error processing file: {str(e)}", status=400)