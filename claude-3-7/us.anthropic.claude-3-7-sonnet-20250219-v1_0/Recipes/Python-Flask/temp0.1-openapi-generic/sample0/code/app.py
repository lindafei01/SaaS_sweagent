
from flask import Flask, request, jsonify, render_template, abort
import sqlite3
import uuid
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

# Database setup
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create recipes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recipes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create comments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        recipe_id TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    )
    ''')
    
    # Create ratings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id TEXT PRIMARY KEY,
        recipe_id TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to convert row to dict
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Helper function to get a recipe by ID
def get_recipe(recipe_id):
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # Get recipe details
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    
    if recipe:
        # Get comments
        cursor.execute('SELECT comment FROM comments WHERE recipe_id = ?', (recipe_id,))
        comments = cursor.fetchall()
        recipe['comments'] = comments
        
        # Get average rating
        cursor.execute('SELECT AVG(rating) as avg_rating FROM ratings WHERE recipe_id = ?', (recipe_id,))
        avg_rating = cursor.fetchone()
        recipe['avgRating'] = avg_rating['avg_rating'] if avg_rating and avg_rating['avg_rating'] else None
        
        # Convert ingredients from string to list
        recipe['ingredients'] = recipe['ingredients'].split('|')
    
    conn.close()
    return recipe

# Routes
@app.route('/recipes', methods=['GET'])
def get_recipes():
    conn = get_db_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    # Get recent recipes
    cursor.execute('SELECT id, title FROM recipes ORDER BY created_at DESC LIMIT 10')
    recent_recipes = cursor.fetchall()
    
    # Get top-rated recipes
    cursor.execute('''
    SELECT r.id, r.title, AVG(rt.rating) as avg_rating 
    FROM recipes r 
    LEFT JOIN ratings rt ON r.id = rt.recipe_id 
    GROUP BY r.id 
    ORDER BY avg_rating DESC
    LIMIT 10
    ''')
    top_recipes = cursor.fetchall()
    
    conn.close()
    
    # For testing purposes, return JSON instead of HTML
    return jsonify({
        'recent_recipes': recent_recipes,
        'top_recipes': top_recipes
    })

@app.route('/recipes/upload', methods=['POST'])
def upload_recipe():
    data = request.json
    
    # Validate required fields
    if not data or not all(key in data for key in ['title', 'ingredients', 'instructions']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate data types and sanitize input
    if not isinstance(data['title'], str) or len(data['title'].strip()) == 0:
        return jsonify({'error': 'Title must be a non-empty string'}), 400
        
    if not isinstance(data['ingredients'], list) or len(data['ingredients']) == 0:
        return jsonify({'error': 'Ingredients must be a non-empty list'}), 400
        
    for ingredient in data['ingredients']:
        if not isinstance(ingredient, str) or len(ingredient.strip()) == 0:
            return jsonify({'error': 'Each ingredient must be a non-empty string'}), 400
            
    if not isinstance(data['instructions'], str) or len(data['instructions'].strip()) == 0:
        return jsonify({'error': 'Instructions must be a non-empty string'}), 400
    
    # Generate unique ID
    recipe_id = str(uuid.uuid4())
    
    # Convert ingredients list to string for storage
    ingredients_str = '|'.join([ingredient.strip() for ingredient in data['ingredients']])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert recipe
    cursor.execute(
        'INSERT INTO recipes (id, title, ingredients, instructions) VALUES (?, ?, ?, ?)',
        (recipe_id, data['title'].strip(), ingredients_str, data['instructions'].strip())
    )
    
    conn.commit()
    conn.close()
    
    # Return created recipe
    recipe = get_recipe(recipe_id)
    return jsonify(recipe), 201

@app.route('/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    recipe = get_recipe(recipe_id)
    
    if not recipe:
        return abort(404)
    
    # For testing purposes, return JSON instead of HTML
    return jsonify(recipe)

@app.route('/recipes/<recipe_id>/comments', methods=['POST'])
def add_comment(recipe_id):
    # Check if recipe exists
    recipe = get_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    data = request.json
    
    # Validate required fields
    if not data or 'comment' not in data:
        return jsonify({'error': 'Comment is required'}), 400
        
    # Validate data types and sanitize input
    if not isinstance(data['comment'], str) or len(data['comment'].strip()) == 0:
        return jsonify({'error': 'Comment must be a non-empty string'}), 400
    
    # Generate unique ID
    comment_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert comment
    cursor.execute(
        'INSERT INTO comments (id, recipe_id, comment) VALUES (?, ?, ?)',
        (comment_id, recipe_id, data['comment'].strip())
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Comment added successfully'}), 201

@app.route('/recipes/<recipe_id>/ratings', methods=['POST'])
def rate_recipe(recipe_id):
    # Check if recipe exists
    recipe = get_recipe(recipe_id)
    if not recipe:
        return jsonify({'error': 'Recipe not found'}), 404
    
    data = request.json
    
    # Validate required fields
    if not data or 'rating' not in data:
        return jsonify({'error': 'Rating is required'}), 400
    
    # Validate rating range
    rating = data['rating']
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    
    # Generate unique ID
    rating_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert rating
    cursor.execute(
        'INSERT INTO ratings (id, recipe_id, rating) VALUES (?, ?, ?)',
        (rating_id, recipe_id, rating)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Rating added successfully'}), 201

# Create templates directory if it doesn't exist
if not os.path.exists('templates'):
    os.makedirs('templates')

# Create templates
def create_templates():
    # Create recipes overview template
    with open('templates/recipes.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Recipe Sharing App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1, h2 { color: #333; }
        .recipe-list { margin-bottom: 30px; }
        .recipe-item { margin: 10px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Recipe Sharing App</h1>
    
    <div class="recipe-list">
        <h2>Recent Recipes</h2>
        {% if recent_recipes %}
            {% for recipe in recent_recipes %}
                <div class="recipe-item">
                    <a href="/recipes/{{ recipe.id }}">{{ recipe.title }}</a>
                </div>
            {% endfor %}
        {% else %}
            <p>No recipes available.</p>
        {% endif %}
    </div>
    
    <div class="recipe-list">
        <h2>Top-Rated Recipes</h2>
        {% if top_recipes %}
            {% for recipe in top_recipes %}
                <div class="recipe-item">
                    <a href="/recipes/{{ recipe.id }}">{{ recipe.title }}</a>
                    {% if recipe.avg_rating %}
                        ({{ recipe.avg_rating|round(1) }} ★)
                    {% endif %}
                </div>
            {% endfor %}
        {% else %}
            <p>No rated recipes available.</p>
        {% endif %}
    </div>
    
    <div>
        <h2>Upload a New Recipe</h2>
        <p>Use the API endpoint POST /recipes/upload to add a new recipe.</p>
    </div>
</body>
</html>
        ''')
    
    # Create recipe detail template
    with open('templates/recipe_detail.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>{{ recipe.title }} - Recipe Sharing App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        h1, h2 { color: #333; }
        .recipe-section { margin-bottom: 20px; }
        .ingredients-list { list-style-type: disc; margin-left: 20px; }
        .rating { color: #f8ce0b; font-size: 18px; }
        .comment { background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 5px; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <a href="/recipes">&larr; Back to all recipes</a>
    
    <h1>{{ recipe.title }}</h1>
    
    {% if recipe.avgRating %}
        <div class="rating">
            {{ recipe.avgRating|round(1) }} ★
        </div>
    {% endif %}
    
    <div class="recipe-section">
        <h2>Ingredients</h2>
        <ul class="ingredients-list">
            {% for ingredient in recipe.ingredients %}
                <li>{{ ingredient }}</li>
            {% endfor %}
        </ul>
    </div>
    
    <div class="recipe-section">
        <h2>Instructions</h2>
        <p>{{ recipe.instructions }}</p>
    </div>
    
    <div class="recipe-section">
        <h2>Comments</h2>
        {% if recipe.comments %}
            {% for comment_obj in recipe.comments %}
                <div class="comment">
                    {{ comment_obj.comment }}
                </div>
            {% endfor %}
        {% else %}
            <p>No comments yet.</p>
        {% endif %}
    </div>
    
    <div class="recipe-section">
        <h2>Add Your Feedback</h2>
        <p>Use the API endpoints:</p>
        <ul>
            <li>POST /recipes/{{ recipe.id }}/comments - to add a comment</li>
            <li>POST /recipes/{{ recipe.id }}/ratings - to rate this recipe (1-5)</li>
        </ul>
    </div>
</body>
</html>
        ''')

create_templates()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)