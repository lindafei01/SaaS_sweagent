
import os
import csv
import sqlite3
import io
from flask import Flask, request, jsonify, render_template_string, make_response
import jwt
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create merchants table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS merchants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    
    # Create wares table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merchant_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        FOREIGN KEY (merchant_id) REFERENCES merchants (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Authentication helper functions
def generate_token(email):
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload['email']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_merchant_id_from_email(email):
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM merchants WHERE email = ?', (email,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def authenticate():
    auth_cookie = request.cookies.get('AUTH_COOKIE')
    if not auth_cookie:
        return None
    
    email = verify_token(auth_cookie)
    if not email:
        return None
    
    return email

# Routes
@app.route('/merchants/register', methods=['POST'])
def register_merchant():
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ['email', 'name', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    email = data['email']
    name = data['name']
    password = data['password']
    
    # Hash the password
    hashed_password = pbkdf2_sha256.hash(password)
    
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO merchants (email, name, password) VALUES (?, ?, ?)',
            (email, name, hashed_password)
        )
        conn.commit()
        conn.close()
        return jsonify({'message': 'Merchant registered successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/merchants/login', methods=['POST'])
def login_merchant():
    data = request.get_json()
    
    if not all(key in data for key in ['email', 'password']):
        return jsonify({'error': 'Missing email or password'}), 400
    
    email = data['email']
    password = data['password']
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM merchants WHERE email = ?', (email,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or not pbkdf2_sha256.verify(password, result[0]):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Generate JWT token
    token = generate_token(email)
    
    # Create response with cookie
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie('AUTH_COOKIE', token, httponly=True, secure=False, samesite='Lax')
    
    return response

@app.route('/merchants/upload-wares', methods=['POST'])
def upload_wares():
    email = authenticate()
    if not email:
        return jsonify({'error': 'Unauthorized'}), 401
    
    merchant_id = get_merchant_id_from_email(email)
    if not merchant_id:
        return jsonify({'error': 'Merchant not found'}), 401
    
    data = request.get_json()
    if 'csv' not in data:
        return jsonify({'error': 'CSV data is required'}), 400
    
    csv_data = data['csv']
    
    try:
        # Parse CSV data
        csv_file = io.StringIO(csv_data)
        csv_reader = csv.reader(csv_file)
        
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        for row in csv_reader:
            if len(row) < 3:
                continue  # Skip invalid rows
            
            name = row[0].strip()
            description = row[1].strip()
            
            try:
                price = float(row[2].strip())
                if price < 0:
                    continue  # Skip negative prices
            except ValueError:
                continue  # Skip rows with invalid price
            
            cursor.execute(
                'INSERT INTO wares (merchant_id, name, description, price) VALUES (?, ?, ?, ?)',
                (merchant_id, name, description, price)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Wares uploaded successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/wares', methods=['GET'])
def get_wares():
    # Authentication is optional for this endpoint according to the schema
    
    # Get filter parameters
    min_price = request.args.get('minPrice', type=float)
    max_price = request.args.get('maxPrice', type=float)
    
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
    SELECT w.name, w.description, w.price, m.email
    FROM wares w
    JOIN merchants m ON w.merchant_id = m.id
    '''
    
    params = []
    where_clauses = []
    
    if min_price is not None:
        where_clauses.append('w.price >= ?')
        params.append(min_price)
    
    if max_price is not None:
        where_clauses.append('w.price <= ?')
        params.append(max_price)
    
    if where_clauses:
        query += ' WHERE ' + ' AND '.join(where_clauses)
    
    cursor.execute(query, params)
    wares = cursor.fetchall()
    conn.close()
    
    # Create HTML table
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Available Wares</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
        </style>
    </head>
    <body>
        <h1>Available Wares</h1>
        <table>
            <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Price</th>
                <th>Merchant</th>
            </tr>
            {% for ware in wares %}
            <tr>
                <td>{{ ware.name }}</td>
                <td>{{ ware.description }}</td>
                <td>${{ "%.2f"|format(ware.price) }}</td>
                <td>{{ ware.email }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    
    return render_template_string(html_template, wares=wares)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)