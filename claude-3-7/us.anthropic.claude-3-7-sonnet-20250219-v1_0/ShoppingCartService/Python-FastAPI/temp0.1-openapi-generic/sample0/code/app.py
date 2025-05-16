
import sqlite3
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import List, Optional

# Initialize FastAPI app
app = FastAPI(title="Shopping Cart Service", description="A simple shopping cart service API.")

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
        cart_id TEXT,
        item_id INTEGER,
        count INTEGER,
        PRIMARY KEY (cart_id, item_id),
        FOREIGN KEY (cart_id) REFERENCES carts(cart_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models for request/response validation
class CartResponse(BaseModel):
    cart_id: str

class AddToCartRequest(BaseModel):
    cart_id: str
    item_id: int
    count: int

class RetrieveCartRequest(BaseModel):
    cart_id: str

class CartItem(BaseModel):
    item_id: int
    count: int

class CartItemsResponse(BaseModel):
    items: List[CartItem]

# API Endpoints
@app.post("/create_cart", status_code=201, response_model=CartResponse)
async def create_cart():
    """Create a new shopping cart"""
    cart_id = str(uuid.uuid4())
    
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO carts (cart_id) VALUES (?)", (cart_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
    
    return {"cart_id": cart_id}

@app.post("/add_to_cart", status_code=200)
async def add_to_cart(request: AddToCartRequest):
    """Add or remove items from the cart"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if cart exists
        cursor.execute("SELECT 1 FROM carts WHERE cart_id = ?", (request.cart_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Check if item already exists in cart
        cursor.execute(
            "SELECT count FROM cart_items WHERE cart_id = ? AND item_id = ?", 
            (request.cart_id, request.item_id)
        )
        existing_item = cursor.fetchone()
        
        if existing_item:
            current_count = existing_item[0]
            new_count = current_count + request.count
            
            if new_count <= 0:
                # Remove item if count becomes zero or negative
                cursor.execute(
                    "DELETE FROM cart_items WHERE cart_id = ? AND item_id = ?",
                    (request.cart_id, request.item_id)
                )
            else:
                # Update item count
                cursor.execute(
                    "UPDATE cart_items SET count = ? WHERE cart_id = ? AND item_id = ?",
                    (new_count, request.cart_id, request.item_id)
                )
        else:
            # Only add new item if count is positive
            if request.count <= 0:
                conn.close()
                raise HTTPException(status_code=400, detail="Cannot add item with zero or negative count")
            
            # Add new item to cart
            cursor.execute(
                "INSERT INTO cart_items (cart_id, item_id, count) VALUES (?, ?, ?)",
                (request.cart_id, request.item_id, request.count)
            )
        
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
    
    return {}

@app.post("/retrieve_cart", status_code=200, response_model=CartItemsResponse)
async def retrieve_cart(request: RetrieveCartRequest):
    """Retrieve all items in the cart"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Check if cart exists
        cursor.execute("SELECT 1 FROM carts WHERE cart_id = ?", (request.cart_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Cart not found")
        
        # Get all items in cart
        cursor.execute(
            "SELECT item_id, count FROM cart_items WHERE cart_id = ?",
            (request.cart_id,)
        )
        items = [{"item_id": item[0], "count": item[1]} for item in cursor.fetchall()]
        
    except sqlite3.Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
    
    return {"items": items}

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)