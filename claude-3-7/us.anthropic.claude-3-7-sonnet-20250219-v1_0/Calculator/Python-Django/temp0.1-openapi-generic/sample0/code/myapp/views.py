
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

def evaluate_expression(expression):
    """
    Safely evaluate a mathematical expression.
    
    This function uses a simple tokenization and evaluation approach
    to calculate the result of basic arithmetic expressions.
    """
    # Remove all whitespace
    expression = expression.replace(" ", "")
    
    # Check if the expression contains only allowed characters
    if not re.match(r'^[0-9+\-*/().]+$', expression):
        raise ValueError("Invalid characters in expression")
    
    # Simple security check to prevent code execution
    if any(keyword in expression for keyword in ['__', 'eval', 'exec', 'import', 'open']):
        raise ValueError("Potentially unsafe expression")
    
    try:
        # Use Python's built-in eval with restricted globals/locals
        # This is safer than raw eval but still needs the input validation above
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {str(e)}")

@csrf_exempt
@require_http_methods(["POST"])
def calculator(request):
    """
    API endpoint to calculate the result of an arithmetic expression.
    
    Accepts a JSON payload with an 'expression' field.
    Returns a JSON response with the 'result' field.
    """
    try:
        # Parse the JSON request body
        data = json.loads(request.body)
        
        # Check if the expression field exists
        if 'expression' not in data:
            return JsonResponse({"error": "Missing 'expression' field"}, status=400)
        
        expression = data['expression']
        
        # Validate that expression is a string
        if not isinstance(expression, str):
            return JsonResponse({"error": "Expression must be a string"}, status=400)
        
        # Evaluate the expression
        result = evaluate_expression(expression)
        
        # Return the result
        return JsonResponse({"result": result})
    
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        # Log the error in a production environment
        return JsonResponse({"error": "Internal server error"}, status=500)