
import json
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def decide_unsubscribe(request):
    """
    Endpoint to decide whether a user requested to be unsubscribed from a mailing list
    
    Args:
        request: HTTP request with raw email content in the body
        
    Returns:
        JsonResponse with email address and unsubscribe decision
    """
    # Get the raw email content from the request body
    email_content = request.body.decode('utf-8')
    
    # Extract the email address from the From header
    email_address = extract_email_address(email_content)
    
    # Check if the email content contains unsubscribe keywords
    unsubscribe_decision = should_unsubscribe(email_content)
    
    # Return the response as JSON
    response_data = {
        'email': email_address,
        'unsubscribe': unsubscribe_decision
    }
    
    return JsonResponse(response_data)

def extract_email_address(email_content):
    """
    Extract the email address from the From header of the email
    
    Args:
        email_content: Raw email content as string
        
    Returns:
        Email address as string or empty string if not found
    """
    # Look for the From header in the email content
    from_match = re.search(r'From:.*?<([^>]+)>', email_content)
    
    if from_match:
        return from_match.group(1).strip()
    
    # If no match with angle brackets, try to find email directly
    from_line_match = re.search(r'From:\s*([^\r\n<]+@[^\r\n>]+)', email_content)
    if from_line_match:
        return from_line_match.group(1).strip()
    
    return ""

def should_unsubscribe(email_content):
    """
    Determine if the email content indicates a request to unsubscribe
    
    Args:
        email_content: Raw email content as string
        
    Returns:
        Boolean indicating whether the user should be unsubscribed
    """
    # Convert to lowercase for case-insensitive matching
    content_lower = email_content.lower()
    
    # Define keywords that indicate an unsubscribe request
    unsubscribe_keywords = [
        'unsubscribe', 
        'remove me', 
        'stop sending', 
        'opt out', 
        'opt-out',
        'take me off',
        'don\'t send',
        'do not send',
        'remove from list',
        'remove from mailing list'
    ]
    
    # Check if any of the unsubscribe keywords are in the email content
    for keyword in unsubscribe_keywords:
        if keyword in content_lower:
            return True
    
    return False