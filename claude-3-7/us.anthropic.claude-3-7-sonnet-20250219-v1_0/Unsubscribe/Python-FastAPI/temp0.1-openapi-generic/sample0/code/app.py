
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import email
import re
import uvicorn

app = FastAPI(
    title="UnsubscribeApp",
    description="UnsubscribeApp provides a simple endpoint to decide whether a user requested to be unsubscribed from a mailing list",
    version="1.0.11"
)

# Common unsubscribe phrases that might appear in email replies
UNSUBSCRIBE_PATTERNS = [
    r"(?i)unsubscribe",
    r"(?i)remove me",
    r"(?i)stop sending",
    r"(?i)opt[ -]?out",
    r"(?i)take me off",
    r"(?i)don'?t (?:send|email|contact)",
    r"(?i)no (?:more|longer) (?:send|email|contact)",
    r"(?i)remove (?:from|me from) (?:list|mailing list)",
]

@app.post("/decideUnsubscribe")
async def decide_unsubscribe(request: Request):
    """
    Expects a raw E-Mail from a user (i.e. reply to a mailing list) and returns 
    whether the user should be unsubscribed and the user E-Mail address
    """
    # Get the raw email content
    raw_email = await request.body()
    raw_email_str = raw_email.decode("utf-8", errors="ignore")
    
    # Parse the email
    email_message = email.message_from_string(raw_email_str)
    
    # Extract the sender's email address
    from_header = email_message.get("From", "")
    email_address = extract_email_address(from_header)
    
    # Extract the email body
    email_body = extract_email_body(email_message)
    
    # Decide if the user wants to unsubscribe
    should_unsubscribe = check_unsubscribe_intent(email_body)
    
    # Return the decision
    return {
        "email": email_address,
        "unsubscribe": should_unsubscribe
    }

def extract_email_address(from_header):
    """Extract email address from the From header."""
    # Try to find an email address in angle brackets (e.g., "Name <email@example.com>")
    match = re.search(r'<([^<>]+@[^<>]+)>', from_header)
    if match:
        return match.group(1)
    
    # If no angle brackets, try to find a plain email address
    match = re.search(r'([^\s<>]+@[^\s<>]+)', from_header)
    if match:
        return match.group(1)
    
    # If no email address found, return the original header
    return from_header

def extract_email_body(email_message):
    """Extract the text content from the email message."""
    body = ""
    
    if email_message.is_multipart():
        # If the message is multipart, find the text/plain part
        for part in email_message.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode("utf-8", errors="ignore")
    else:
        # If the message is not multipart, get the payload directly
        payload = email_message.get_payload(decode=True)
        if payload:
            body = payload.decode("utf-8", errors="ignore")
    
    return body

def check_unsubscribe_intent(email_body):
    """Check if the email body contains phrases indicating an intent to unsubscribe."""
    # Check each unsubscribe pattern
    for pattern in UNSUBSCRIBE_PATTERNS:
        if re.search(pattern, email_body):
            return True
    
    return False

if __name__ == "__main__":
    # Run the FastAPI application with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)