
import os
import sqlite3
import jwt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from passlib.hash import pbkdf2_sha256
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Create secrets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS secrets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        secret TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in the header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Invalid authentication token'}), 401
        
        try:
            # Decode the token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Check if user exists
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
            current_user = cursor.fetchone()
            conn.close()
            
            if not current_user:
                return jsonify({'message': 'Invalid authentication token'}), 401
                
        except Exception as e:
            return jsonify({'message': 'Invalid authentication token'}), 401
            
        return f(*args, **kwargs)
    
    return decorated
# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input data
    if not data or not data.get('email') or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Email, username, and password are required'}), 400
    
    # Hash the password
    hashed_password = pbkdf2_sha256.hash(data['password'])
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
        if cursor.fetchone():
            return jsonify({'message': 'Email already in use'}), 400
        
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
        if cursor.fetchone():
            return jsonify({'message': 'Username already in use'}), 400
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
            (data['email'], data['username'], hashed_password)
        )
        conn.commit()
        
        return jsonify({'message': 'Registration successful'}), 201
    
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400
    
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input data
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password are required'}), 400
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (data['email'],))
        user = cursor.fetchone()
        
        if not user or not pbkdf2_sha256.verify(data['password'], user[3]):
            return jsonify({'message': 'Invalid email or password'}), 401
        
        # Generate token
        token = jwt.encode(
            {
                'email': user[1],
                'username': user[2],
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            'token': token,
            'message': 'Login successful'
        }), 200
    
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400
    
    finally:
        conn.close()

@app.route('/set_secret', methods=['POST'])
@token_required
def set_secret():
    data = request.get_json()
    
    # Validate input data
    if not data or not data.get('username') or not data.get('secret'):
        return jsonify({'message': 'Username and secret are required'}), 400
    
    # Get token data
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if username exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Check if the token belongs to the user or if the user is trying to set someone else's secret
        if token_data['username'] != data['username']:
            return jsonify({'message': 'Unauthorized to set secret for this user'}), 401
        
        # Check if secret already exists for this user
        cursor.execute("SELECT * FROM secrets WHERE username = ?", (data['username'],))
        existing_secret = cursor.fetchone()
        
        if existing_secret:
            # Update existing secret
            cursor.execute(
                "UPDATE secrets SET secret = ? WHERE username = ?",
                (data['secret'], data['username'])
            )
        else:
            # Insert new secret
            cursor.execute(
                "INSERT INTO secrets (username, secret) VALUES (?, ?)",
                (data['username'], data['secret'])
            )
        
        conn.commit()
        
        return jsonify({'message': 'Secret has been set successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400
    
    finally:
        conn.close()

@app.route('/get_secret', methods=['GET'])
@token_required
def get_secret():
    # Get username from query parameters
    username = request.args.get('username')
    
    if not username:
        return jsonify({'message': 'Username is required'}), 400
    
    # Get token data
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if the token belongs to the user or if the user is trying to get someone else's secret
        if token_data['username'] != username:
            return jsonify({'message': 'Unauthorized to get secret for this user'}), 401
        
        # Get secret
        cursor.execute("SELECT secret FROM secrets WHERE username = ?", (username,))
        secret = cursor.fetchone()
        
        if not secret:
            return jsonify({'message': 'Secret not found'}), 404
        
        return jsonify({'secret': secret[0]}), 200
    
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 400
    
    finally:
        conn.close()

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)