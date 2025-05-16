
import os
import re
from django.http import JsonResponse
from django.conf import settings
import json


def search(request):
    """
    Search files in a specified directory and return files whose content matches the given regex.
    """
    # Get parameters from request
    regex_pattern = request.GET.get('regex')
    directory = request.GET.get('directory', '')
    recursive = request.GET.get('recursive', 'false').lower() == 'true'
    
    # Validate regex pattern
    if not regex_pattern:
        return JsonResponse({'error': 'Regex pattern is required'}, status=400)
    
    # Validate and sanitize directory path to prevent directory traversal
    base_dir = os.path.join(settings.FILES_ROOT, directory.lstrip('/'))
    base_dir = os.path.normpath(base_dir)
    
    # Ensure the path is within the FILES_ROOT directory
    if not base_dir.startswith(settings.FILES_ROOT):
        return JsonResponse({'error': 'Invalid directory path'}, status=400)
    
    # Check if directory exists
    if not os.path.isdir(base_dir):
        return JsonResponse({'error': f'Directory not found: {directory}'}, status=400)
    
    # Compile regex pattern
    try:
        pattern = re.compile(regex_pattern)
    except re.error:
        return JsonResponse({'error': 'Invalid regex pattern'}, status=400)
    
    # Search for files matching the regex
    matching_files = []
    
    try:
        if recursive:
            # Walk through all subdirectories
            for root, _, files in os.walk(base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if _file_matches_pattern(file_path, pattern):
                        # Get relative path from the search directory
                        rel_path = os.path.relpath(file_path, base_dir)
                        matching_files.append(rel_path)
        else:
            # Only search in the specified directory
            for file in os.listdir(base_dir):
                file_path = os.path.join(base_dir, file)
                if os.path.isfile(file_path) and _file_matches_pattern(file_path, pattern):
                    matching_files.append(file)
    except Exception as e:
        return JsonResponse({'error': f'Error searching files: {str(e)}'}, status=500)
    
    return JsonResponse({'files': matching_files})


def _file_matches_pattern(file_path, pattern):
    """
    Check if the file content matches the given regex pattern.
    """
    try:
        # Skip binary files
        if _is_binary_file(file_path):
            return False
            
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
            return bool(pattern.search(content))
    except Exception:
        # Skip files that can't be read
        return False


def _is_binary_file(file_path):
    """
    Check if a file is binary by reading a chunk and looking for null bytes.
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except Exception:
        return True  # If we can't read the file, treat it as binary