
from fastapi import FastAPI, Query, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Recommendation",
    description="Product recommendation service to provide a list of posted products searched by tag.",
    version="1.0.11"
)

# Define data models
class ProductCreate(BaseModel):
    product_name: str
    tags: List[str]

# Database setup
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL
    )
    ''')
    
    # Create tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create product_tags junction table for many-to-many relationship
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_tags (
        product_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (product_id, tag_id),
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Create templates directory for HTML responses
templates = Jinja2Templates(directory="templates")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Create a simple HTML template for product listing
with open("templates/products.html", "w") as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Product Recommendations</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            color: #333;
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
    <p>Showing products matching tags: {{ tags }}</p>
    
    {% if products %}
        {% for product in products %}
        <div class="product">
            <h3>{{ product.product_name }}</h3>
            <div>
                {% for tag in product.tags %}
                <span class="tag">{{ tag }}</span>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    {% else %}
        <p>No products found matching these tags.</p>
    {% endif %}
</body>
</html>
''')

# API Endpoints
@app.get("/recommender", response_class=HTMLResponse)
async def get_recommendations(request: Request, tags: str = Query(..., description="Tags to search for separated by comma.")):
    # Split the comma-separated tags
    tag_list = [tag.strip() for tag in tags.split(",")]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get products that match at least one of the provided tags
    query = '''
    SELECT DISTINCT p.id, p.product_name
    FROM products p
    JOIN product_tags pt ON p.id = pt.product_id
    JOIN tags t ON pt.tag_id = t.id
    WHERE t.tag_name IN ({})
    '''.format(','.join(['?'] * len(tag_list)))
    
    cursor.execute(query, tag_list)
    products = cursor.fetchall()
    
    # For each product, get its tags
    product_data = []
    for product in products:
        cursor.execute('''
        SELECT t.tag_name
        FROM tags t
        JOIN product_tags pt ON t.id = pt.tag_id
        WHERE pt.product_id = ?
        ''', (product['id'],))
        
        product_tags = [row['tag_name'] for row in cursor.fetchall()]
        product_data.append({
            'product_name': product['product_name'],
            'tags': product_tags
        })
    
    conn.close()
    
    # Return HTML response using the template
    return templates.TemplateResponse(
        "products.html", 
        {"request": request, "products": product_data, "tags": tags}
    )

@app.post("/recommender")
async def create_product(product: ProductCreate):
    if not product.product_name or not product.tags:
        raise HTTPException(status_code=400, detail="Product name and tags are required")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert product
        cursor.execute("INSERT INTO products (product_name) VALUES (?)", (product.product_name,))
        product_id = cursor.lastrowid
        
        # Insert tags and create relationships
        for tag_name in product.tags:
            # Try to insert the tag (if it doesn't exist)
            try:
                cursor.execute("INSERT INTO tags (tag_name) VALUES (?)", (tag_name,))
                tag_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                # Tag already exists, get its ID
                cursor.execute("SELECT id FROM tags WHERE tag_name = ?", (tag_name,))
                tag_id = cursor.fetchone()['id']
            
            # Create relationship between product and tag
            cursor.execute("INSERT INTO product_tags (product_id, tag_id) VALUES (?, ?)", 
                          (product_id, tag_id))
        
        conn.commit()
        return {"status": "success", "message": "Product created successfully"}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating product: {str(e)}")
    
    finally:
        conn.close()

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)