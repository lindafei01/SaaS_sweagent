
import os
import sqlite3
import uuid
import re
from flask import Flask, request, jsonify
from passlib.hash import pbkdf2_sha256
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create invitations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invite_id TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

def is_valid_email(email):
    """Check if email is valid using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Routes
@app.route('/invite_user', methods=['POST'])
def invite_user():
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'message': 'Email is required'}), 400
    
    email = data['email']
    
    if not is_valid_email(email):
        return jsonify({'message': 'Invalid email format'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email already has an invitation
    cursor.execute('SELECT invite_id FROM invitations WHERE email = ?', (email,))
    existing_invite = cursor.fetchone()
    
    if existing_invite:
        # Return existing invitation
        invite_id = existing_invite['invite_id']
        conn.close()
        return jsonify({
            'invite_id': invite_id,
            'message': 'Invitation already exists for this email'
        })
    
    # Generate a new invitation
    invite_id = str(uuid.uuid4())
    
    try:
        cursor.execute('INSERT INTO invitations (invite_id, email) VALUES (?, ?)', 
                      (invite_id, email))
        conn.commit()
        conn.close()
        
        return jsonify({
            'invite_id': invite_id,
            'message': 'Invitation created successfully'
        })
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Error creating invitation'}), 500

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data or 'invite_id' not in data or 'user_name' not in data or 'password' not in data:
        return jsonify({'message': 'Invite ID, username, and password are required'}), 400
    
    invite_id = data['invite_id']
    user_name = data['user_name']
    password = data['password']
    
    # Validate inputs
    if not invite_id or not user_name or not password:
        return jsonify({'message': 'All fields must be non-empty'}), 400
    
    if len(password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters long'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if invitation exists
    cursor.execute('SELECT email FROM invitations WHERE invite_id = ?', (invite_id,))
    invitation = cursor.fetchone()
    
    if not invitation:
        conn.close()
        return jsonify({'message': 'Invalid invite_id'}), 401
    
    email = invitation['email']
    
    # Check if username already exists
    cursor.execute('SELECT id FROM users WHERE user_name = ?', (user_name,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Username already exists. Try providing different username.'}), 400
    
    # Hash the password
    hashed_password = pbkdf2_sha256.hash(password)
    
    try:
        # Create the user
        cursor.execute('INSERT INTO users (user_name, password, email) VALUES (?, ?, ?)',
                      (user_name, hashed_password, email))
        
        # Delete the invitation
        cursor.execute('DELETE FROM invitations WHERE invite_id = ?', (invite_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User created successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Error creating user'}), 500

# Initialize database when the app starts
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)