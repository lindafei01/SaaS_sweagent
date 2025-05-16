
#!/usr/bin/env python3
import os
import json
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        properties TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

@app.route('/add', methods=['POST'])
def add_product():
    """Add a new product to the catalog."""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Name is required'}), 400
        
        name = data.pop('name')
        
        # Store remaining properties as JSON
        properties = json.dumps(data)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO products (name, properties) VALUES (?, ?)',
                (name, properties)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Product with this name already exists'}), 400
        
        conn.close()
        return jsonify({'message': 'Product added successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['GET'])
def download_product():
    """Download product data by name."""
    try:
        name = request.args.get('name')
        
        if not name:
            return jsonify({'error': 'Name parameter is required'}), 400
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT properties FROM products WHERE name = ?',
            (name,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Product not found'}), 404
        
        # Return the product data
        return jsonify({'data': result[0]}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/upload', methods=['POST'])
def upload_product():
    """Upload data for a product."""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'data' not in data:
            return jsonify({'error': 'Name and data are required'}), 400
        
        name = data['name']
        product_data = data['data']
        
        # Validate that product_data is a valid JSON string
        try:
            json.loads(product_data)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid data format'}), 400
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
        product = cursor.fetchone()
        
        if product:
            # Update existing product
            cursor.execute(
                'UPDATE products SET properties = ? WHERE name = ?',
                (product_data, name)
            )
        else:
            # Create new product
            cursor.execute(
                'INSERT INTO products (name, properties) VALUES (?, ?)',
                (name, product_data)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Product updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/search', methods=['GET'])
def search_products():
    """Search for products in the catalog."""
    try:
        query = request.args.get('query')
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Search in name and properties
        cursor.execute(
            'SELECT name, properties FROM products WHERE name LIKE ? OR properties LIKE ?',
            (f'%{query}%', f'%{query}%')
        )
        
        results = []
        for row in cursor.fetchall():
            product = {'name': row['name']}
            
            # Add all properties from the JSON
            properties = json.loads(row['properties'])
            product.update(properties)
            
            results.append(product)
        
        conn.close()
        
        return jsonify({'results': results}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)