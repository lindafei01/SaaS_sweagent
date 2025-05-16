
#!/usr/bin/env python3
import os
import sqlite3
import io
import re
from flask import Flask, request, jsonify, send_file, abort, Response, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        username TEXT PRIMARY KEY,
        profile_page TEXT NOT NULL,
        profile_photo BLOB NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Helper functions for security
def validate_username(username):
    """Validate username to prevent malicious input"""
    # Only allow alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    return True

def sanitize_html(html_content):
    """Basic sanitization of HTML content"""
    # This is a very basic sanitization - in production, use a proper HTML sanitizer library
    # Remove potentially dangerous tags and attributes
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'onerror=',
        r'onclick=',
        r'onload=',
        r'onmouseover=',
        r'<iframe.*?>.*?</iframe>',
        r'<object.*?>.*?</object>',
        r'<embed.*?>.*?</embed>'
    ]
    
    sanitized = html_content
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized

# Initialize the database on startup
init_db()

@app.route('/add_profile', methods=['POST'])
def add_profile():
    # Check if all required fields are present
    if 'username' not in request.form or 'profile_page' not in request.form or 'profile_photo' not in request.files:
        return jsonify({'error': 'Missing required fields'}), 400
    
    username = request.form['username']
    profile_page = request.form['profile_page']
    profile_photo = request.files['profile_photo']
    
    # Validate inputs
    if not username or not profile_page or not profile_photo:
        return jsonify({'error': 'Empty fields not allowed'}), 400
    
    # Validate username format
    if not validate_username(username):
        return jsonify({'error': 'Username must contain only alphanumeric characters and underscores'}), 400
    
    # Validate profile photo is PNG
    if not profile_photo.filename.lower().endswith('.png'):
        return jsonify({'error': 'Profile photo must be a PNG image'}), 400
    
    # Sanitize HTML content
    profile_page = sanitize_html(profile_page)
    
    # Secure the username to prevent SQL injection
    username = secure_filename(username)
    
    # Read the profile photo
    profile_photo_data = profile_photo.read()
    
    # Check if profile already exists
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM profiles WHERE username = ?', (username,))
    existing_profile = cursor.fetchone()
    
    if existing_profile:
        conn.close()
        return jsonify({'error': 'Profile already exists'}), 403
    
    # Store the profile in the database
    try:
        cursor.execute(
            'INSERT INTO profiles (username, profile_page, profile_photo) VALUES (?, ?, ?)',
            (username, profile_page, profile_photo_data)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Profile created successfully'}), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/profile/<username>', methods=['GET'])
def get_profile(username):
    # Validate username format
    if not validate_username(username):
        return jsonify({'error': 'Invalid username format'}), 400
    
    # Secure the username to prevent SQL injection
    username = secure_filename(username)
    
    # Retrieve the profile from the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT profile_page FROM profiles WHERE username = ?', (username,))
    profile = cursor.fetchone()
    conn.close()
    
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404
    
    # Return the HTML content
    return Response(profile[0], mimetype='text/html')

@app.route('/profile-photo/<username>', methods=['GET'])
def get_profile_photo(username):
    # Validate username format
    if not validate_username(username):
        return jsonify({'error': 'Invalid username format'}), 400
    
    # Secure the username to prevent SQL injection
    username = secure_filename(username)
    
    # Retrieve the profile photo from the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT profile_photo FROM profiles WHERE username = ?', (username,))
    profile_photo = cursor.fetchone()
    conn.close()
    
    if not profile_photo:
        return jsonify({'error': 'Profile photo not found'}), 404
    
    # Return the PNG image
    return send_file(
        io.BytesIO(profile_photo[0]),
        mimetype='image/png',
        as_attachment=False
    )

@app.route('/', methods=['GET'])
def index():
    """Display a simple form for adding profiles"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profile Manager</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            form { margin-bottom: 20px; }
            label { display: block; margin: 10px 0 5px; }
            input, textarea { margin-bottom: 10px; }
            button { padding: 8px 16px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Profile Manager</h1>
        <h2>Add a New Profile</h2>
        <form action="/add_profile" method="post" enctype="multipart/form-data">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required>
            
            <label for="profile_page">Profile Page (HTML):</label>
            <textarea id="profile_page" name="profile_page" rows="10" cols="50" required></textarea>
            
            <label for="profile_photo">Profile Photo (PNG only):</label>
            <input type="file" id="profile_photo" name="profile_photo" accept="image/png" required>
            
            <button type="submit">Add Profile</button>
        </form>
        
        <h2>View Existing Profiles</h2>
        <p>To view a profile, go to: /profile/&lt;username&gt;</p>
        <p>To view a profile photo, go to: /profile-photo/&lt;username&gt;</p>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)