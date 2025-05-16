
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
import uuid
import os
import difflib
import markdown
from pathlib import Path

# Create the app
app = FastAPI(title="Wiki API", description="API for a simple wiki where users can add and edit entries, with change tracking.")

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

# Create templates
with open(templates_dir / "base.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Wiki{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .entry { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .entry-title { margin-top: 0; }
        .entry-meta { color: #666; font-size: 0.9em; margin-bottom: 10px; }
        .entry-content { margin-top: 10px; }
        .diff-added { background-color: #e6ffed; color: #22863a; }
        .diff-removed { background-color: #ffeef0; color: #cb2431; }
        .edit-history { margin-top: 20px; }
        .edit-item { border-bottom: 1px solid #eee; padding: 10px 0; }
    </style>
</head>
<body>
    <header>
        <h1><a href="/entries">Wiki</a></h1>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
    """)

with open(templates_dir / "entries.html", "w") as f:
    f.write("""
{% extends "base.html" %}
{% block title %}All Wiki Entries{% endblock %}
{% block content %}
    <h1>All Wiki Entries</h1>
    <div class="entries">
        {% if entries %}
            {% for entry in entries %}
                <div class="entry">
                    <h2 class="entry-title"><a href="/entries/{{ entry.id }}">{{ entry.title }}</a></h2>
                    <div class="entry-meta">
                        Last modified by {{ entry.lastModifiedBy }} on {{ entry.lastModifiedAt }}
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p>No entries yet. Create the first one!</p>
        {% endif %}
    </div>
{% endblock %}
    """)

with open(templates_dir / "entry.html", "w") as f:
    f.write("""
{% extends "base.html" %}
{% block title %}{{ entry.title }}{% endblock %}
{% block content %}
    <div class="entry">
        <h1 class="entry-title">{{ entry.title }}</h1>
        <div class="entry-meta">
            Last modified by {{ entry.lastModifiedBy }} on {{ entry.lastModifiedAt }}
            <a href="/entries/{{ entry.id }}/edits">(View History)</a>
        </div>
        <div class="entry-content">
            {{ content|safe }}
        </div>
    </div>
{% endblock %}
    """)

with open(templates_dir / "edits.html", "w") as f:
    f.write("""
{% extends "base.html" %}
{% block title %}Edit History for {{ entry.title }}{% endblock %}
{% block content %}
    <h1>Edit History for "{{ entry.title }}"</h1>
    <a href="/entries/{{ entry.id }}">Back to Entry</a>
    
    <div class="edit-history">
        {% for edit in edits %}
            <div class="edit-item">
                <h3>Edit by {{ edit.modifiedBy }} on {{ edit.modifiedAt }}</h3>
                {% if edit.summary %}
                    <p><strong>Summary:</strong> {{ edit.summary }}</p>
                {% endif %}
                <div class="diff">
                    {{ edit.diff|safe }}
                </div>
            </div>
        {% endfor %}
    </div>
{% endblock %}
    """)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create entries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_modified_by TEXT NOT NULL,
        last_modified_at TEXT NOT NULL
    )
    ''')
    
    # Create edits table to track changes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS edits (
        id TEXT PRIMARY KEY,
        entry_id TEXT NOT NULL,
        content TEXT NOT NULL,
        modified_by TEXT NOT NULL,
        modified_at TEXT NOT NULL,
        summary TEXT,
        FOREIGN KEY (entry_id) REFERENCES entries (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Database connection helper
def get_db():
    conn = sqlite3.connect('db.sqlite3', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class NewEntry(BaseModel):
    title: str
    content: str
    createdBy: str

class UpdateEntry(BaseModel):
    content: str
    modifiedBy: str
    summary: Optional[str] = None

class Entry(BaseModel):
    id: str
    title: str
    content: str
    lastModifiedBy: str
    lastModifiedAt: str

# Helper function to generate HTML diff
def generate_diff_html(old_content, new_content):
    diff = difflib.ndiff(old_content.splitlines(), new_content.splitlines())
    html_diff = []
    
    for line in diff:
        if line.startswith('+ '):
            html_diff.append(f'<div class="diff-added">{line[2:]}</div>')
        elif line.startswith('- '):
            html_diff.append(f'<div class="diff-removed">{line[2:]}</div>')
        elif line.startswith('? '):
            continue
        else:
            html_diff.append(f'<div>{line[2:]}</div>')
    
    return ''.join(html_diff)

# API Routes
@app.get("/entries", response_class=HTMLResponse)
async def get_entries(request: Request, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM entries ORDER BY last_modified_at DESC")
    entries = cursor.fetchall()
    
    # Convert to list of dicts
    entries_list = []
    for entry in entries:
        entries_list.append({
            "id": entry["id"],
            "title": entry["title"],
            "lastModifiedBy": entry["last_modified_by"],
            "lastModifiedAt": entry["last_modified_at"]
        })
    
    return templates.TemplateResponse("entries.html", {"request": request, "entries": entries_list})

@app.post("/entries", response_model=Entry, status_code=201)
async def create_entry(entry: NewEntry, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Generate a unique ID
    entry_id = str(uuid.uuid4())
    current_time = datetime.now().isoformat()
    
    # Insert the new entry
    cursor.execute(
        "INSERT INTO entries (id, title, content, created_by, created_at, last_modified_by, last_modified_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (entry_id, entry.title, entry.content, entry.createdBy, current_time, entry.createdBy, current_time)
    )
    
    # Also record this as the first edit
    edit_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO edits (id, entry_id, content, modified_by, modified_at, summary) VALUES (?, ?, ?, ?, ?, ?)",
        (edit_id, entry_id, entry.content, entry.createdBy, current_time, "Initial creation")
    )
    
    db.commit()
    
    return {
        "id": entry_id,
        "title": entry.title,
        "content": entry.content,
        "lastModifiedBy": entry.createdBy,
        "lastModifiedAt": current_time
    }

@app.get("/entries/{entry_id}", response_class=HTMLResponse)
async def get_entry(request: Request, entry_id: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Convert to dict
    entry_dict = {
        "id": entry["id"],
        "title": entry["title"],
        "content": entry["content"],
        "lastModifiedBy": entry["last_modified_by"],
        "lastModifiedAt": entry["last_modified_at"]
    }
    
    # Convert markdown content to HTML
    html_content = markdown.markdown(entry["content"])
    
    return templates.TemplateResponse("entry.html", {
        "request": request, 
        "entry": entry_dict,
        "content": html_content
    })

@app.put("/entries/{entry_id}", response_model=Entry)
async def update_entry(entry_id: str, update: UpdateEntry, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Check if entry exists
    cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    current_time = datetime.now().isoformat()
    
    # Get the current content for diff generation
    old_content = entry["content"]
    
    # Update the entry
    cursor.execute(
        "UPDATE entries SET content = ?, last_modified_by = ?, last_modified_at = ? WHERE id = ?",
        (update.content, update.modifiedBy, current_time, entry_id)
    )
    
    # Record this edit
    edit_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO edits (id, entry_id, content, modified_by, modified_at, summary) VALUES (?, ?, ?, ?, ?, ?)",
        (edit_id, entry_id, update.content, update.modifiedBy, current_time, update.summary)
    )
    
    db.commit()
    
    return {
        "id": entry_id,
        "title": entry["title"],
        "content": update.content,
        "lastModifiedBy": update.modifiedBy,
        "lastModifiedAt": current_time
    }

@app.get("/entries/{entry_id}/edits", response_class=HTMLResponse)
async def get_entry_edits(request: Request, entry_id: str, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    
    # Check if entry exists
    cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Get all edits for this entry
    cursor.execute(
        "SELECT * FROM edits WHERE entry_id = ? ORDER BY modified_at DESC",
        (entry_id,)
    )
    edits = cursor.fetchall()
    
    # Convert to list of dicts with diffs
    edits_with_diffs = []
    previous_content = None
    
    for i, edit in enumerate(reversed(edits)):
        current_content = edit["content"]
        
        if previous_content:
            diff_html = generate_diff_html(previous_content, current_content)
        else:
            # For the first edit, just show the content as added
            diff_html = generate_diff_html("", current_content)
        
        edits_with_diffs.append({
            "modifiedBy": edit["modified_by"],
            "modifiedAt": edit["modified_at"],
            "summary": edit["summary"],
            "diff": diff_html
        })
        
        previous_content = current_content
    
    # Reverse back to show newest first
    edits_with_diffs.reverse()
    
    # Convert entry to dict
    entry_dict = {
        "id": entry["id"],
        "title": entry["title"]
    }
    
    return templates.TemplateResponse("edits.html", {
        "request": request,
        "entry": entry_dict,
        "edits": edits_with_diffs
    })

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)