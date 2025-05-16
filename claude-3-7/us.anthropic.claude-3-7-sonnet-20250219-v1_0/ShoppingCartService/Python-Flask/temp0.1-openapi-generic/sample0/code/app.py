
#!/usr/bin/env python3
import os
import uuid
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create carts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS carts (
        cart_id TEXT PRIMARY KEY
    )
    ''')
    
    # Create cart_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cart_id TEXT,
        item_id INTEGER,
        count INTEGER,
        FOREIGN KEY (cart_id) REFERENCES carts (cart_id),
        UNIQUE(cart_id, item_id)
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

@app.route('/create_cart', methods=['POST'])
def create_cart():
    # Generate a unique cart ID
    cart_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO carts (cart_id) VALUES (?)', (cart_id,))
        conn.commit()
        return jsonify({'cart_id': cart_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    
    # Validate required fields
    if not all(key in data for key in ['cart_id', 'item_id', 'count']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    cart_id = data['cart_id']
    item_id = data['item_id']
    count = data['count']
    
    # Validate data types
    if not isinstance(item_id, int) or not isinstance(count, int):
        return jsonify({'error': 'item_id and count must be integers'}), 400
    
    conn = get_db_connection()
    try:
        # Check if cart exists
        cart = conn.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,)).fetchone()
        if not cart:
            return jsonify({'error': 'Cart not found'}), 404
        
        # Check if item already exists in cart
        item = conn.execute('SELECT * FROM cart_items WHERE cart_id = ? AND item_id = ?', 
                           (cart_id, item_id)).fetchone()
        
        if item:
            # Update existing item count
            new_count = item['count'] + count
            if new_count <= 0:
                # Remove item if count becomes zero or negative
                conn.execute('DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?', 
                            (cart_id, item_id))
            else:
                # Update count
                conn.execute('UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?', 
                            (new_count, cart_id, item_id))
        else:
            # Only add new item if count is positive
            if count > 0:
                conn.execute('INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)', 
                            (cart_id, item_id, count))
        
        conn.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/retrieve_cart', methods=['POST'])
def retrieve_cart():
    data = request.get_json()
    
    # Validate required fields
    if 'cart_id' not in data:
        return jsonify({'error': 'Missing cart_id field'}), 400
    
    cart_id = data['cart_id']
    
    conn = get_db_connection()
    try:
        # Check if cart exists
        cart = conn.execute('SELECT * FROM carts WHERE cart_id = ?', (cart_id,)).fetchone()
        if not cart:
            return jsonify({'error': 'Cart not found'}), 404
        
        # Get all items in the cart
        items = conn.execute('''
            SELECT item_id, count FROM cart_items 
            WHERE cart_id = ? AND count > 0
        ''', (cart_id,)).fetchall()
        
        # Convert to list of dictionaries
        items_list = [{'item_id': item['item_id'], 'count': item['count']} for item in items]
        
        return jsonify({'items': items_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)