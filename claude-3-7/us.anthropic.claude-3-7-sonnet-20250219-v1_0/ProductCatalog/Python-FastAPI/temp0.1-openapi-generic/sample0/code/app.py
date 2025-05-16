
import sqlite3
import json
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Product Catalog",
    description="Provides product catalog allowing multiple unstructured properties to be given and then searched for.",
    version="1.0.11"
)

# Database setup
DB_NAME = "db.sqlite3"

def get_db_connection():
    """Create a database connection and return it"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    # Ensure the database directory exists
    db_dir = os.path.dirname(os.path.abspath(DB_NAME))
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        properties TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Models
class ProductBase(BaseModel):
    name: str

class ProductAdd(ProductBase):
    # This model allows additional properties
    class Config:
        extra = "allow"

class ProductUpload(BaseModel):
    name: str
    data: str

class ProductDownload(BaseModel):
    data: str

class SearchResult(BaseModel):
    results: List[Dict[str, str]]

# Endpoints
@app.post("/add", status_code=201)
async def add_product(product: ProductAdd):
    """Add a new product to the catalog"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Extract name and additional properties
        name = product.name
        # Remove name from the dict and keep the rest as properties
        product_dict = product.model_dump()
        product_dict.pop("name", None)
        
        # Store properties as JSON string
        properties_json = json.dumps(product_dict)
        
        cursor.execute(
            "INSERT INTO products (name, properties) VALUES (?, ?)",
            (name, properties_json)
        )
        
        conn.commit()
        conn.close()
        
        return {"message": "Product successfully added"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Product with this name already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

@app.get("/download")
async def download_product(name: str = Query(..., description="The name of the product")):
    """Download the entire current catalog with its unstructured properties for a given product name"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, properties FROM products WHERE name = ?", (name,))
        product = cursor.fetchone()
        
        conn.close()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Combine name and properties into a single data object
        product_data = {
            "name": product["name"],
            **json.loads(product["properties"])
        }
        
        # Return the data as a JSON string
        return {"data": json.dumps(product_data)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.post("/upload")
async def upload_product(upload: ProductUpload):
    """Upload data for a product with the given name in the catalog"""
    try:
        # Parse the data string as JSON
        try:
            product_data = json.loads(upload.data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON data")
        
        if not isinstance(product_data, dict):
            raise HTTPException(status_code=400, detail="Data must be a JSON object")
        
        # Ensure the name in the data matches the name in the request
        if "name" not in product_data or product_data["name"] != upload.name:
            raise HTTPException(status_code=400, detail="Product name in data must match the name parameter")
        
        # Extract name and properties
        name = upload.name
        product_data.pop("name", None)  # Remove name from properties
        properties_json = json.dumps(product_data)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
        product = cursor.fetchone()
        
        if product:
            # Update existing product
            cursor.execute(
                "UPDATE products SET properties = ? WHERE name = ?",
                (properties_json, name)
            )
        else:
            # Insert new product
            cursor.execute(
                "INSERT INTO products (name, properties) VALUES (?, ?)",
                (name, properties_json)
            )
        
        conn.commit()
        conn.close()
        
        return {"message": "Product updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.get("/search", response_model=SearchResult)
async def search_products(query: str = Query(..., description="A search query to find matching products")):
    """Search for products in the catalog"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search in both name and properties
        # Using LIKE for simple text search
        search_term = f"%{query}%"
        
        cursor.execute(
            "SELECT name, properties FROM products WHERE name LIKE ? OR properties LIKE ?",
            (search_term, search_term)
        )
        
        products = cursor.fetchall()
        conn.close()
        
        results = []
        for product in products:
            # Combine name and properties
            product_data = {
                "name": product["name"],
                **json.loads(product["properties"])
            }
            results.append(product_data)
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid search query: {str(e)}")

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)