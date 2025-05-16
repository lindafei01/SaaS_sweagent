
#!/usr/bin/env python3
import os
import sqlite3
from flask import Flask, request, jsonify, render_template_string, g

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
DATABASE = 'db.sqlite3'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT NOT NULL UNIQUE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_tags (
                product_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (product_id, tag_id),
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id)
            )
        ''')
        db.commit()

# HTML template for displaying products
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Product Recommendations</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .product {
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
        }
        .tag {
            background-color: #f0f0f0;
            padding: 3px 8px;
            margin-right: 5px;
            border-radius: 3px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <h1>Product Recommendations</h1>
    {% if products %}
        {% for product in products %}
            <div class="product">
                <h2>{{ product.product_name }}</h2>
                <div>
                    <strong>Tags:</strong>
                    {% for tag in product.tags %}
                        <span class="tag">{{ tag }}</span>
                    {% endfor %}
                </div>
            </div>
        {% endfor %}
    {% else %}
        <p>No products found matching your search criteria.</p>
    {% endif %}
</body>
</html>
'''

@app.route('/recommender', methods=['GET'])
def get_recommendations():
    tags_param = request.args.get('tags')
    
    if not tags_param:
        return "Missing required 'tags' parameter", 400
    
    # Split the tags by comma and sanitize
    search_tags = [tag.strip() for tag in tags_param.split(',')]
    
    db = get_db()
    cursor = db.cursor()
    
    # Get products that match at least one of the provided tags
    query = '''
    SELECT DISTINCT p.id, p.product_name
    FROM products p
    JOIN product_tags pt ON p.id = pt.product_id
    JOIN tags t ON pt.tag_id = t.id
    WHERE t.tag_name IN ({})
    '''.format(','.join(['?'] * len(search_tags)))
    
    cursor.execute(query, search_tags)
    product_rows = cursor.fetchall()
    
    products = []
    for row in product_rows:
        # Get all tags for this product
        cursor.execute('''
            SELECT t.tag_name
            FROM tags t
            JOIN product_tags pt ON t.id = pt.tag_id
            WHERE pt.product_id = ?
        ''', (row['id'],))
        
        product_tags = [tag['tag_name'] for tag in cursor.fetchall()]
        
        products.append({
            'product_name': row['product_name'],
            'tags': product_tags
        })
    
    return render_template_string(HTML_TEMPLATE, products=products)

@app.route('/recommender', methods=['POST'])
def add_product():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    product_name = data.get('product_name')
    tags = data.get('tags', [])
    
    if not product_name:
        return jsonify({"error": "Product name is required"}), 400
    
    if not isinstance(tags, list):
        return jsonify({"error": "Tags must be an array"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Insert product
        cursor.execute('INSERT INTO products (product_name) VALUES (?)', (product_name,))
        product_id = cursor.lastrowid
        
        # Process tags
        for tag in tags:
            # Insert tag if it doesn't exist
            cursor.execute('INSERT OR IGNORE INTO tags (tag_name) VALUES (?)', (tag,))
            
            # Get tag ID
            cursor.execute('SELECT id FROM tags WHERE tag_name = ?', (tag,))
            tag_id = cursor.fetchone()['id']
            
            # Link product to tag
            cursor.execute('INSERT INTO product_tags (product_id, tag_id) VALUES (?, ?)', 
                          (product_id, tag_id))
        
        db.commit()
        return jsonify({"message": "Product added successfully"}), 200
    
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)