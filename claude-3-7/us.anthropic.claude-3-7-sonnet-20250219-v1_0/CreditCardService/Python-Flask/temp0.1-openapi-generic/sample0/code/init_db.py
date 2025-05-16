
#!/usr/bin/env python3
import sqlite3
import os

DB_NAME = 'db.sqlite3'

def init_db():
    try:
        print("Initializing database...")
        
        # Remove existing database if it exists
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE card_phone_associations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_card TEXT NOT NULL,
            phone TEXT NOT NULL,
            UNIQUE(credit_card, phone)
        )
        ''')
        
        conn.commit()
        
        # Verify table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='card_phone_associations'")
        if cursor.fetchone():
            print("Table created successfully")
        else:
            print("Failed to create table")
        
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_db()