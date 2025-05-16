
#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_id TEXT NOT NULL,
        token TEXT NOT NULL,
        last_notification TIMESTAMP NOT NULL,
        UNIQUE(service_id, token)
    )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/heartbeat', methods=['POST'])
def register_heartbeat():
    try:
        data = request.get_json()
        
        # Validate request payload
        if not data or 'serviceId' not in data or 'token' not in data:
            return jsonify({'error': 'Invalid request payload'}), 400
        
        service_id = data['serviceId']
        token = data['token']
        
        # Sanitize inputs to prevent SQL injection
        if not isinstance(service_id, str) or not isinstance(token, str):
            return jsonify({'error': 'Invalid data types'}), 400
            
        current_time = datetime.utcnow().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if service exists with this token
        cursor.execute(
            'SELECT * FROM services WHERE service_id = ? AND token = ?',
            (service_id, token)
        )
        service = cursor.fetchone()
        
        if service:
            # Update existing service
            cursor.execute(
                'UPDATE services SET last_notification = ? WHERE service_id = ? AND token = ?',
                (current_time, service_id, token)
            )
        else:
            # Insert new service
            cursor.execute(
                'INSERT INTO services (service_id, token, last_notification) VALUES (?, ?, ?)',
                (service_id, token, current_time)
            )
            
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Heartbeat registered successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/services', methods=['POST'])
def get_services():
    try:
        data = request.get_json()
        
        # Validate request payload
        if not data or 'token' not in data:
            return jsonify({'error': 'Invalid request payload'}), 400
            
        token = data['token']
        
        # Sanitize inputs to prevent SQL injection
        if not isinstance(token, str):
            return jsonify({'error': 'Invalid data types'}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all services registered with the given token
        cursor.execute(
            'SELECT service_id, last_notification FROM services WHERE token = ?',
            (token,)
        )
        services = cursor.fetchall()
        
        result = []
        for service in services:
            result.append({
                'serviceId': service['service_id'],
                'lastNotification': service['last_notification']
            })
            
        conn.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)