
import os
import sqlite3
import datetime
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

# Create FastAPI app
app = FastAPI(
    title="MyForum",
    description="MyForum is a simple webapp that allows users to post and read messages.",
    version="1.0.11"
)

# Add session middleware for security
app_secret = os.environ.get("APP_SECRET", "default_secret_key_for_development")
app.add_middleware(SessionMiddleware, secret_key=app_secret)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Create base HTML template
with open("templates/base.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>MyForum</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .message {
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .username {
            font-weight: bold;
            color: #333;
        }
        .timestamp {
            color: #999;
            font-size: 0.8em;
        }
        .content {
            margin-top: 5px;
        }
        form {
            margin-top: 20px;
            margin-bottom: 20px;
        }
        input, textarea {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h1>MyForum</h1>
    {% block content %}{% endblock %}
</body>
</html>""")

# Create index template
with open("templates/index.html", "w") as f:
    f.write("""{% extends "base.html" %}
{% block content %}
    <form id="messageForm">
        <h2>Post a new message</h2>
        <div>
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div>
            <label for="content">Message:</label>
            <textarea id="content" name="content" rows="4" required></textarea>
        </div>
        <button type="submit">Post Message</button>
    </form>
    
    <h2>Messages</h2>
    <div id="messages">
        {% for message in messages %}
        <div class="message">
            <div class="username">{{ message.username }}</div>
            <div class="timestamp">{{ message.timestamp }}</div>
            <div class="content">{{ message.content }}</div>
        </div>
        {% endfor %}
    </div>

    <script>
        document.getElementById('messageForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const content = document.getElementById('content').value;
            
            try {
                const response = await fetch('/messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, content }),
                });
                
                if (response.ok) {
                    // Reload the page to show the new message
                    window.location.reload();
                } else {
                    alert('Error posting message');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error posting message');
            }
        });
    </script>
{% endblock %}""")

# Define sorting direction enum
class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

# Define message model
class Message(BaseModel):
    content: str
    username: str

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        username TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Database connection dependency
def get_db():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Routes
@app.get("/messages", response_class=HTMLResponse)
async def get_messages(
    request: Request,
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    sort: SortDirection = Query(SortDirection.DESC),
    db: sqlite3.Connection = Depends(get_db)
):
    # Sanitize inputs to prevent SQL injection
    sort_direction = "ASC" if sort == SortDirection.ASC else "DESC"
    
    cursor = db.cursor()
    cursor.execute(
        f"SELECT * FROM messages ORDER BY timestamp {sort_direction} LIMIT ? OFFSET ?",
        (limit, offset)
    )
    messages = cursor.fetchall()
    
    # Convert to list of dicts for template
    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg["id"],
            "content": msg["content"],
            "username": msg["username"],
            "timestamp": msg["timestamp"]
        })
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "messages": message_list}
    )

@app.post("/messages")
async def post_message(message: Message, db: sqlite3.Connection = Depends(get_db)):
    # Validate input
    if not message.content or not message.username:
        raise HTTPException(status_code=400, detail="Content and username are required")
    
    # Sanitize input to prevent SQL injection
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO messages (content, username) VALUES (?, ?)",
        (message.content, message.username)
    )
    db.commit()
    
    return {"status": "success"}

# Root redirect to messages
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "messages": []})

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)