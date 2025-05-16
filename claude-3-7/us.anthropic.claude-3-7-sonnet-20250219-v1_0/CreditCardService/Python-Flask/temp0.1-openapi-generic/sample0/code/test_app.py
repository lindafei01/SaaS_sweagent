
#!/usr/bin/env python3
import sqlite3
import requests
import json
import os

# Clean up any existing database
if os.path.exists('db.sqlite3'):
    os.remove('db.sqlite3')

BASE_URL = 'http://0.0.0.0:5000'

def test_associate_card():
    print("Testing associate_card endpoint...")
    
    # Test case 1: Valid association
    response = requests.post(
        f"{BASE_URL}/associate_card",
        json={"credit_card": "1234-5678-9012-3456", "phone": "+1-555-123-4567"}
    )
    print(f"Test case 1 - Status code: {response.status_code}")
    print(f"Response content: {response.text}")
    assert response.status_code == 201
    
    # Test case 2: Another valid association with the same card
    response = requests.post(
        f"{BASE_URL}/associate_card",
        json={"credit_card": "1234-5678-9012-3456", "phone": "+1-555-987-6543"}
    )
    print(f"Test case 2 - Status code: {response.status_code}")
    assert response.status_code == 201
    
    # Test case 3: Another card with the first phone
    response = requests.post(
        f"{BASE_URL}/associate_card",
        json={"credit_card": "9876-5432-1098-7654", "phone": "+1-555-123-4567"}
    )
    print(f"Test case 3 - Status code: {response.status_code}")
    assert response.status_code == 201
    
    # Test case 4: Missing fields
    response = requests.post(
        f"{BASE_URL}/associate_card",
        json={"credit_card": "1234-5678-9012-3456"}
    )
    print(f"Test case 4 - Status code: {response.status_code}")
    assert response.status_code == 400
    
    print("All associate_card tests passed!\n")

def test_retrieve_cards():
    print("Testing retrieve_cards endpoint...")
    
    # Test case 1: Retrieve card associated with one phone
    response = requests.post(
        f"{BASE_URL}/retrieve_cards",
        json={"phone_numbers": ["+1-555-123-4567"]}
    )
    print(f"Test case 1 - Status code: {response.status_code}")
    print(f"Response content: {response.text}")
    assert response.status_code == 200
    data = response.json()
    print(f"Retrieved cards: {data['card_numbers']}")
    assert len(data['card_numbers']) == 2
    assert "1234-5678-9012-3456" in data['card_numbers']
    assert "9876-5432-1098-7654" in data['card_numbers']
    
    # Test case 2: Retrieve card associated with two phones
    response = requests.post(
        f"{BASE_URL}/retrieve_cards",
        json={"phone_numbers": ["+1-555-123-4567", "+1-555-987-6543"]}
    )
    print(f"Test case 2 - Status code: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    print(f"Retrieved cards: {data['card_numbers']}")
    assert len(data['card_numbers']) == 1
    assert "1234-5678-9012-3456" in data['card_numbers']
    
    # Test case 3: No matching cards
    response = requests.post(
        f"{BASE_URL}/retrieve_cards",
        json={"phone_numbers": ["+1-555-123-4567", "+1-555-987-6543", "+1-555-000-0000"]}
    )
    print(f"Test case 3 - Status code: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    print(f"Retrieved cards: {data['card_numbers']}")
    assert len(data['card_numbers']) == 0
    
    # Test case 4: Invalid request (missing phone_numbers)
    response = requests.post(
        f"{BASE_URL}/retrieve_cards",
        json={}
    )
    print(f"Test case 4 - Status code: {response.status_code}")
    assert response.status_code == 400
    
    print("All retrieve_cards tests passed!")

if __name__ == "__main__":
    print("Starting tests...")
    try:
        test_associate_card()
        test_retrieve_cards()
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nError during testing: {e}")