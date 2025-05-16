
#!/usr/bin/env python3
from flask import Flask, request, jsonify
import re
import email

app = Flask(__name__)

def extract_email_from_header(header_value):
    """Extract email address from a header value like 'Name <email@example.com>'"""
    if not header_value:
        return None
    
    # Try to extract email from format "Name <email@example.com>"
    email_match = re.search(r'<([^<>]+@[^<>]+)>', header_value)
    if email_match:
        return email_match.group(1)
    
    # If no angle brackets, try to extract just the email
    email_match = re.search(r'([^\s<>]+@[^\s<>]+\.[^\s<>]+)', header_value)
    if email_match:
        return email_match.group(1)
    
    return None

def check_unsubscribe_intent(email_content):
    """Check if the email content indicates an unsubscribe intent"""
    # Convert to lowercase for case-insensitive matching
    content_lower = email_content.lower()
    
    # List of phrases that might indicate unsubscribe intent
    unsubscribe_phrases = [
        'unsubscribe', 
        'remove me', 
        'opt out', 
        'stop sending', 
        'take me off', 
        'don\'t send',
        'remove from list',
        'stop emails'
    ]
    
    # Check if any unsubscribe phrase is in the content
    for phrase in unsubscribe_phrases:
        if phrase in content_lower:
            return True
    
    return False

@app.route('/decideUnsubscribe', methods=['POST'])
def decide_unsubscribe():
    """
    Endpoint to decide if a user wants to unsubscribe based on email content
    """
    if not request.data:
        return jsonify({"error": "No email content provided"}), 400
    
    # Parse the raw email
    try:
        raw_email = request.data.decode('utf-8', errors='replace')
        email_message = email.message_from_string(raw_email)
        
        # Extract the sender's email address
        from_header = email_message.get('From', '')
        sender_email = extract_email_from_header(from_header)
        
        if not sender_email:
            return jsonify({"error": "Could not extract sender email"}), 400
        
        # Extract email content
        email_content = ""
        
        # Handle multipart emails
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        email_content += payload.decode('utf-8', errors='replace')
        else:
            # Handle single part emails
            payload = email_message.get_payload(decode=True)
            if payload:
                email_content += payload.decode('utf-8', errors='replace')
        
        # Determine if the user wants to unsubscribe
        should_unsubscribe = check_unsubscribe_intent(email_content)
        
        # Return the decision
        return jsonify({
            "email": sender_email,
            "unsubscribe": should_unsubscribe
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)