
from flask import Flask, request, jsonify, render_template_string, abort
import sqlite3
import uuid
from datetime import datetime
import difflib
import html

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create entries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_by TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        last_modified_by TEXT NOT NULL,
        last_modified_at TIMESTAMP NOT NULL
    )
    ''')
    
    # Create edits table to track history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_id TEXT NOT NULL,
        content TEXT NOT NULL,
        modified_by TEXT NOT NULL,
        modified_at TIMESTAMP NOT NULL,
        summary TEXT,
        FOREIGN KEY (entry_id) REFERENCES entries (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# HTML templates as simple strings
BASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Wiki - {{title}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .entry { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
        .entry-title { margin-top: 0; }
        .entry-meta { color: #666; font-size: 0.9em; margin-top: 10px; }
        .btn { display: inline-block; padding: 8px 16px; background: #4CAF50; color: white; 
               text-decoration: none; border-radius: 4px; margin-right: 10px; }
        .btn-edit { background: #2196F3; }
        .btn-back { background: #607D8B; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
        .diff-added { background-color: #e6ffed; color: #22863a; }
        .diff-removed { background-color: #ffeef0; color: #cb2431; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Wiki</h1>
        <div>
            <a href="/" class="btn btn-back">Home</a>
            <a href="/entries" class="btn">All Entries</a>
        </div>
        <hr>
        {{content}}
    </div>
</body>
</html>
'''

# Routes
@app.route('/')
def home():
    content = '''
    <h2>Welcome to the Wiki</h2>
    <p>A simple wiki application where you can create and edit entries.</p>
    <a href="/entries" class="btn">View All Entries</a>
    '''
    return render_template_string(BASE_TEMPLATE.replace('{{content}}', content).replace('{{title}}', 'Home'))

@app.route('/entries', methods=['GET'])
def get_entries():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, last_modified_by, last_modified_at FROM entries ORDER BY last_modified_at DESC')
    entries = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    entries_html = '''
    <h2>All Wiki Entries</h2>
    <a href="#" id="new-entry-btn" class="btn">Create New Entry</a>
    <div id="new-entry-form" style="display: none;" class="entry">
        <h3>Create New Entry</h3>
        <form id="entryForm">
            <div>
                <label for="title">Title:</label><br>
                <input type="text" id="title" name="title" required style="width: 100%; padding: 8px; margin-bottom: 10px;">
            </div>
            <div>
                <label for="content">Content:</label><br>
                <textarea id="content" name="content" rows="10" required style="width: 100%; padding: 8px; margin-bottom: 10px;"></textarea>
            </div>
            <div>
                <label for="createdBy">Your Name:</label><br>
                <input type="text" id="createdBy" name="createdBy" required style="width: 100%; padding: 8px; margin-bottom: 10px;">
            </div>
            <button type="submit" class="btn">Create Entry</button>
            <button type="button" id="cancelBtn" class="btn btn-back">Cancel</button>
        </form>
    </div>
    <div id="entries-list">
    '''
    
    if entries:
        for entry in entries:
            entries_html += f'''
            <div class="entry">
                <h3 class="entry-title"><a href="/entries/{entry['id']}">{entry['title']}</a></h3>
                <div class="entry-meta">
                    Last modified by {entry['last_modified_by']} on {entry['last_modified_at']}
                </div>
            </div>
            '''
    else:
        entries_html += '<p>No entries yet. Be the first to create one!</p>'
    
    entries_html += '''
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const newEntryBtn = document.getElementById('new-entry-btn');
            const newEntryForm = document.getElementById('new-entry-form');
            const cancelBtn = document.getElementById('cancelBtn');
            
            newEntryBtn.addEventListener('click', function(e) {
                e.preventDefault();
                newEntryForm.style.display = 'block';
            });
            
            cancelBtn.addEventListener('click', function() {
                newEntryForm.style.display = 'none';
            });
            
            document.getElementById('entryForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = {
                    title: document.getElementById('title').value,
                    content: document.getElementById('content').value,
                    createdBy: document.getElementById('createdBy').value
                };
                
                fetch('/entries', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    window.location.href = `/entries/${data.id}`;
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to create entry');
                });
            });
        });
    </script>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{content}}', entries_html).replace('{{title}}', 'All Entries'))

@app.route('/entries', methods=['POST'])
def create_entry():
    data = request.json
    
    if not data or 'title' not in data or 'content' not in data or 'createdBy' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    entry_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Sanitize inputs to prevent SQL injection
    cursor.execute('''
    INSERT INTO entries (id, title, content, created_by, created_at, last_modified_by, last_modified_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (entry_id, data['title'], data['content'], data['createdBy'], now, data['createdBy'], now))
    
    # Record the initial creation as the first edit
    cursor.execute('''
    INSERT INTO edits (entry_id, content, modified_by, modified_at, summary)
    VALUES (?, ?, ?, ?, ?)
    ''', (entry_id, data['content'], data['createdBy'], now, 'Initial creation'))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': entry_id,
        'title': data['title'],
        'content': data['content'],
        'lastModifiedBy': data['createdBy'],
        'lastModifiedAt': now
    }), 201

@app.route('/entries/<entry_id>', methods=['GET'])
def get_entry(entry_id):
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    conn.close()
    
    if not entry:
        abort(404)
    
    entry_dict = dict(entry)
    
    entry_html = f'''
    <h2>{entry_dict['title']}</h2>
    <div class="entry-meta">
        Last modified by {entry_dict['last_modified_by']} on {entry_dict['last_modified_at']}
    </div>
    <div class="entry-content">
        <pre>{entry_dict['content']}</pre>
    </div>
    <div class="entry-actions">
        <a href="#" id="edit-btn" class="btn btn-edit">Edit</a>
        <a href="/entries/{entry_dict['id']}/edits" class="btn">View History</a>
    </div>
    
    <div id="edit-form" style="display: none;" class="entry">
        <h3>Edit Entry</h3>
        <form id="updateForm">
            <div>
                <label for="content">Content:</label><br>
                <textarea id="content" name="content" rows="10" required style="width: 100%; padding: 8px; margin-bottom: 10px;">{entry_dict['content']}</textarea>
            </div>
            <div>
                <label for="modifiedBy">Your Name:</label><br>
                <input type="text" id="modifiedBy" name="modifiedBy" required style="width: 100%; padding: 8px; margin-bottom: 10px;">
            </div>
            <div>
                <label for="summary">Edit Summary:</label><br>
                <input type="text" id="summary" name="summary" required style="width: 100%; padding: 8px; margin-bottom: 10px;">
            </div>
            <button type="submit" class="btn">Save Changes</button>
            <button type="button" id="cancelEditBtn" class="btn btn-back">Cancel</button>
        </form>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const editBtn = document.getElementById('edit-btn');
            const editForm = document.getElementById('edit-form');
            const cancelEditBtn = document.getElementById('cancelEditBtn');
            
            editBtn.addEventListener('click', function(e) {{
                e.preventDefault();
                editForm.style.display = 'block';
            }});
            
            cancelEditBtn.addEventListener('click', function() {{
                editForm.style.display = 'none';
            }});
            
            document.getElementById('updateForm').addEventListener('submit', function(e) {{
                e.preventDefault();
                
                const formData = {{
                    content: document.getElementById('content').value,
                    modifiedBy: document.getElementById('modifiedBy').value,
                    summary: document.getElementById('summary').value
                }};
                
                fetch('/entries/{entry_dict['id']}', {{
                    method: 'PUT',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(formData)
                }})
                .then(response => response.json())
                .then(data => {{
                    window.location.reload();
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    alert('Failed to update entry');
                }});
            }});
        }});
    </script>
    '''
    
    return render_template_string(BASE_TEMPLATE.replace('{{content}}', entry_html).replace('{{title}}', entry_dict['title']))

@app.route('/entries/<entry_id>', methods=['PUT'])
def update_entry(entry_id):
    data = request.json
    
    if not data or 'content' not in data or 'modifiedBy' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if entry exists
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        conn.close()
        return jsonify({'error': 'Entry not found'}), 404
    
    now = datetime.utcnow().isoformat()
    
    # Update the entry
    cursor.execute('''
    UPDATE entries 
    SET content = ?, last_modified_by = ?, last_modified_at = ?
    WHERE id = ?
    ''', (data['content'], data['modifiedBy'], now, entry_id))
    
    # Record the edit
    summary = data.get('summary', '')
    cursor.execute('''
    INSERT INTO edits (entry_id, content, modified_by, modified_at, summary)
    VALUES (?, ?, ?, ?, ?)
    ''', (entry_id, data['content'], data['modifiedBy'], now, summary))
    
    conn.commit()
    
    # Get updated entry
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    updated_entry = dict(cursor.fetchone())
    
    conn.close()
    
    return jsonify({
        'id': updated_entry['id'],
        'title': updated_entry['title'],
        'content': updated_entry['content'],
        'lastModifiedBy': updated_entry['last_modified_by'],
        'lastModifiedAt': updated_entry['last_modified_at']
    })

@app.route('/entries/<entry_id>/edits', methods=['GET'])
def get_entry_edits(entry_id):
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if entry exists
    cursor.execute('SELECT * FROM entries WHERE id = ?', (entry_id,))
    entry = cursor.fetchone()
    
    if not entry:
        conn.close()
        abort(404)
    
    entry_dict = dict(entry)
    
    # Get all edits for this entry
    cursor.execute('''
    SELECT e1.id, e1.entry_id, e1.content, e1.modified_by, e1.modified_at, e1.summary,
           e2.content as previous_content
    FROM edits e1
    LEFT JOIN edits e2 ON e1.id = e2.id + 1 AND e1.entry_id = e2.entry_id
    WHERE e1.entry_id = ?
    ORDER BY e1.id DESC
    ''', (entry_id,))
    
    edits_html = f'''
    <h2>Edit History: {entry_dict['title']}</h2>
    <a href="/entries/{entry_dict['id']}" class="btn">Back to Entry</a>
    '''
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            edit = dict(row)
            
            # Generate diff between current and previous version
            diff_html = ''
            if edit['previous_content']:
                diff = difflib.unified_diff(
                    edit['previous_content'].splitlines(),
                    edit['content'].splitlines(),
                    lineterm=''
                )
                
                # Skip the first 3 lines (diff header)
                for _ in range(3):
                    next(diff, None)
                
                # Format the diff for HTML display
                diff_lines = []
                for line in diff:
                    if line.startswith('+'):
                        diff_lines.append(f'<span class="diff-added">{html.escape(line)}</span>')
                    elif line.startswith('-'):
                        diff_lines.append(f'<span class="diff-removed">{html.escape(line)}</span>')
                    else:
                        diff_lines.append(html.escape(line))
                
                diff_html = '\n'.join(diff_lines)
            else:
                # For the first edit, just show the content
                diff_html = f'<span class="diff-added">{html.escape(edit["content"])}</span>'
            
            summary = edit['summary'] if edit['summary'] else ''
            edits_html += f'''
            <div class="entry">
                <h3>Edit by {edit['modified_by']} on {edit['modified_at']}</h3>
                {f'<p><strong>Summary:</strong> {summary}</p>' if summary else ''}
                <div class="diff">
                    <pre>{diff_html}</pre>
                </div>
            </div>
            '''
    else:
        edits_html += '<p>No edit history available.</p>'
    
    conn.close()
    
    return render_template_string(BASE_TEMPLATE.replace('{{content}}', edits_html).replace('{{title}}', f'Edit History - {entry_dict["title"]}'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)