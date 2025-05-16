
#!/usr/bin/env python3
import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET', 'default-secret-key')

# Database setup
DB_NAME = 'db.sqlite3'

def init_db():
    try:
        print("Initializing database...")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS card_phone_associations (
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

# Initialize database on startup
init_db()

# Verify database setup
def verify_db_setup():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='card_phone_associations'")
        if not cursor.fetchone():
            print("Table not found, reinitializing database...")
            init_db()
        conn.close()
    except Exception as e:
        print(f"Database verification error: {e}")
        init_db()

verify_db_setup()

@app.route('/associate_card', methods=['POST'])
def associate_card():
    try:
        data = request.get_json()
        print(f"Received associate_card request: {data}")
        
        if not data or 'credit_card' not in data or 'phone' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        credit_card = data['credit_card'].strip()
        phone = data['phone'].strip()
        
        # Validate input
        if not credit_card or not phone:
            return jsonify({'error': 'Credit card and phone cannot be empty'}), 400
        
        # Store in database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO card_phone_associations (credit_card, phone) VALUES (?, ?)',
                (credit_card, phone)
            )
            conn.commit()
            print(f"Successfully associated card {credit_card} with phone {phone}")
        except sqlite3.IntegrityError:
            # Association already exists, which is fine
            print(f"Association already exists for card {credit_card} with phone {phone}")
            pass
        finally:
            conn.close()
        
        return '', 201
    
    except Exception as e:
        print(f"Error in associate_card: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/retrieve_cards', methods=['POST'])
def retrieve_cards():
    try:
        data = request.get_json()
        print(f"Received retrieve_cards request: {data}")
        
        if not data or 'phone_numbers' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        phone_numbers = data['phone_numbers']
        
        # Validate input
        if not isinstance(phone_numbers, list) or not phone_numbers:
            return jsonify({'error': 'Phone numbers must be a non-empty array'}), 400
        
        # Clean phone numbers
        phone_numbers = [phone.strip() for phone in phone_numbers if phone.strip()]
        print(f"Cleaned phone numbers: {phone_numbers}")
        
        if not phone_numbers:
            return jsonify({'error': 'No valid phone numbers provided'}), 400
        
        # Query database for cards associated with ALL provided phone numbers
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # First, get all cards associated with the first phone number
        cursor.execute(
            'SELECT DISTINCT credit_card FROM card_phone_associations WHERE phone = ?',
            (phone_numbers[0],)
        )
        
        potential_cards = {row[0] for row in cursor.fetchall()}
        print(f"Cards for first phone {phone_numbers[0]}: {potential_cards}")
        
        # If no cards found for the first phone, return empty result
        if not potential_cards:
            conn.close()
            return jsonify({'card_numbers': []}), 200
        
        # For each additional phone number, filter the potential cards
        for phone in phone_numbers[1:]:
            cursor.execute(
                'SELECT DISTINCT credit_card FROM card_phone_associations WHERE phone = ?',
                (phone,)
            )
            
            cards_for_this_phone = {row[0] for row in cursor.fetchall()}
            print(f"Cards for phone {phone}: {cards_for_this_phone}")
            
            # Keep only cards that are associated with this phone too
            potential_cards = potential_cards.intersection(cards_for_this_phone)
            print(f"Filtered potential cards: {potential_cards}")
            
            # If no cards match all phones so far, we can exit early
            if not potential_cards:
                break
        
        conn.close()
        
        # Convert set to list for JSON serialization
        result = list(potential_cards)
        print(f"Final result: {result}")
        
        return jsonify({'card_numbers': result}), 200
    
    except Exception as e:
        print(f"Error in retrieve_cards: {e}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)