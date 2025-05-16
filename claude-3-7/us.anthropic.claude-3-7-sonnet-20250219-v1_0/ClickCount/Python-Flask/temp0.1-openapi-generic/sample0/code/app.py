
#!/usr/bin/env python3
import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create clicks table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clicks (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/click', methods=['POST'])
def register_click():
    """Register a user click in the database."""
    try:
        # Generate a unique ID for the click
        click_id = str(uuid.uuid4())
        
        # Get current timestamp in ISO format
        timestamp = datetime.utcnow().isoformat()
        
        # Store the click in the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clicks (id, timestamp) VALUES (?, ?)', 
                      (click_id, timestamp))
        conn.commit()
        conn.close()
        
        return '', 201  # Return 201 Created status code
    except Exception as e:
        app.logger.error(f"Error registering click: {str(e)}")
        return jsonify({"error": "Failed to register click"}), 400

@app.route('/clicks', methods=['GET'])
def get_clicks():
    """Retrieve clicks before or after a specified date."""
    try:
        # Get query parameters
        date_param = request.args.get('date')
        direction = request.args.get('direction')
        
        # Validate parameters
        if not date_param or not direction:
            return jsonify({"error": "Missing required parameters: date and direction"}), 400
        
        if direction not in ['<', '>', '<=', '>=']:
            return jsonify({"error": "Invalid direction parameter. Must be <, >, <= or >="}), 400
        
        # Try to parse the date to validate format
        try:
            # Convert date string to datetime object for comparison
            filter_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Build the SQL query based on the direction parameter
        query = f"SELECT id, timestamp FROM clicks WHERE DATE(timestamp) {direction} ?"
        
        # Execute the query
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (date_param,))
        
        # Fetch all matching clicks
        clicks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not clicks:
            return jsonify({"error": "No clicks found for the specified criteria"}), 404
        
        return jsonify(clicks), 200
    
    except Exception as e:
        app.logger.error(f"Error retrieving clicks: {str(e)}")
        return jsonify({"error": "Failed to retrieve clicks"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)