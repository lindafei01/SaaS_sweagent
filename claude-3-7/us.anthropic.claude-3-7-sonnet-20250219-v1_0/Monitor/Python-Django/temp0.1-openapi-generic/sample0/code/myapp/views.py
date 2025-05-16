
import json
import re
import subprocess
import shlex
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def monitor_commands(request):
    """
    Endpoint to retrieve a list of running processes that match a given regex pattern.
    
    POST parameters:
    - filter_flags: Optional flags to filter and sort processes (e.g., "aux -T")
    - command_regex: Required regex pattern to match against process commands
    
    Returns:
    - JSON array of objects with processId and processString
    """
    try:
        # Parse the request body
        data = json.loads(request.body)
        
        # Check if command_regex is provided
        if 'command_regex' not in data:
            return JsonResponse({"code": 400, "message": "command_regex is required"}, status=400)
        
        command_regex = data['command_regex']
        filter_flags = data.get('filter_flags', 'aux')
        
        # Sanitize inputs to prevent command injection
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', filter_flags):
            return JsonResponse({"code": 400, "message": "Invalid filter_flags"}, status=400)
        
        try:
            # Compile the regex to validate it
            regex_pattern = re.compile(command_regex)
        except re.error:
            return JsonResponse({"code": 400, "message": "Invalid regex pattern"}, status=400)
        
        # Build the ps command
        cmd = f"ps {filter_flags}"
        
        # Execute the command
        try:
            process = subprocess.Popen(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                return JsonResponse({"code": 500, "message": f"Error executing ps command: {stderr}"}, status=500)
            
            # Process the output
            lines = stdout.strip().split('\n')
            
            # Skip the header line
            if len(lines) > 0:
                lines = lines[1:]
            
            result = []
            for line in lines:
                # Extract PID (usually the first or second column)
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                # The PID is typically in the second column for 'aux' format
                try:
                    pid = int(parts[1])
                except (ValueError, IndexError):
                    # If that fails, try the first column
                    try:
                        pid = int(parts[0])
                    except (ValueError, IndexError):
                        continue
                
                # Get the command part (usually everything after the 10th column for 'aux')
                try:
                    # For 'aux' format, command starts at column 11
                    command_idx = 10
                    if len(parts) > command_idx:
                        command = ' '.join(parts[command_idx:])
                    else:
                        command = ' '.join(parts)
                        
                    # Check if the command matches the regex
                    if regex_pattern.search(command):
                        result.append({
                            "processId": pid,
                            "processString": line
                        })
                except Exception as e:
                    # Skip lines that can't be processed
                    continue
            
            return JsonResponse(result, safe=False)
            
        except Exception as e:
            return JsonResponse({"code": 500, "message": f"Server error: {str(e)}"}, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({"code": 400, "message": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        return JsonResponse({"code": 500, "message": f"Server error: {str(e)}"}, status=500)