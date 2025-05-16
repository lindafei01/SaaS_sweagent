
import sqlite3
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Credit Card Phone Association Service",
    description="A simple service to checking credit cards with phones.",
    version="1.0.0"
)

# Database setup
DB_NAME = "db.sqlite3"

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table for card-phone associations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS card_phone_associations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credit_card TEXT NOT NULL,
        phone TEXT NOT NULL,
        UNIQUE(credit_card, phone)
    )
    ''')
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON card_phone_associations(phone)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_card ON card_phone_associations(credit_card)')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models for request/response validation
class CardPhoneAssociation(BaseModel):
    credit_card: str
    phone: str

class PhoneNumbersRequest(BaseModel):
    phone_numbers: List[str]

class CardNumbersResponse(BaseModel):
    card_numbers: List[str]

# API Endpoints
@app.post("/associate_card", status_code=201)
def associate_card(association: CardPhoneAssociation):
    """Create a new association of a credit card number with a phone number."""
    if not association.credit_card or not association.phone:
        raise HTTPException(status_code=400, detail="Credit card and phone number are required")
    
    # Validate input (basic validation)
    if not association.credit_card.strip() or not association.phone.strip():
        raise HTTPException(status_code=400, detail="Credit card and phone number cannot be empty")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert the association, ignore if it already exists
        cursor.execute(
            "INSERT OR IGNORE INTO card_phone_associations (credit_card, phone) VALUES (?, ?)",
            (association.credit_card, association.phone)
        )
        
        conn.commit()
        conn.close()
        
        return {"message": "Association created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create association: {str(e)}")

@app.post("/retrieve_cards", status_code=200)
def retrieve_cards(request: PhoneNumbersRequest):
    """Retrieve cards associated with all given phone numbers."""
    if not request.phone_numbers:
        raise HTTPException(status_code=400, detail="Phone numbers are required")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count how many phone numbers we're looking for
        phone_count = len(request.phone_numbers)
        
        # Find cards that are associated with ALL the provided phone numbers
        placeholders = ','.join(['?'] * phone_count)
        query = f"""
        SELECT credit_card
        FROM card_phone_associations
        WHERE phone IN ({placeholders})
        GROUP BY credit_card
        HAVING COUNT(DISTINCT phone) = ?
        """
        
        # Execute the query with phone numbers and count as parameters
        cursor.execute(query, request.phone_numbers + [phone_count])
        
        # Fetch results
        results = cursor.fetchall()
        card_numbers = [row['credit_card'] for row in results]
        
        conn.close()
        
        if not card_numbers:
            raise HTTPException(status_code=404, detail="No credit cards found for all given phone numbers")
        
        return CardNumbersResponse(card_numbers=card_numbers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve cards: {str(e)}")

# Run the application
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)