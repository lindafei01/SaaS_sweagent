
import requests
import json

BASE_URL = "http://localhost:5000"

def test_associate_card():
    print("Testing associate_card endpoint...")
    
    # Test case 1: Associate a credit card with a phone number
    data = {
        "credit_card": "4111111111111111",
        "phone": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/associate_card", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test case 2: Associate another credit card with the same phone number
    data = {
        "credit_card": "5555555555554444",
        "phone": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/associate_card", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test case 3: Associate the first credit card with another phone number
    data = {
        "credit_card": "4111111111111111",
        "phone": "+0987654321"
    }
    
    response = requests.post(f"{BASE_URL}/associate_card", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

def test_retrieve_cards():
    print("\nTesting retrieve_cards endpoint...")
    
    # Test case 1: Retrieve cards associated with a single phone number
    data = {
        "phone_numbers": ["+1234567890"]
    }
    
    response = requests.post(f"{BASE_URL}/retrieve_cards", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test case 2: Retrieve cards associated with multiple phone numbers
    data = {
        "phone_numbers": ["+1234567890", "+0987654321"]
    }
    
    response = requests.post(f"{BASE_URL}/retrieve_cards", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test case 3: Retrieve cards with non-existent phone number
    data = {
        "phone_numbers": ["+1234567890", "+nonexistent"]
    }
    
    response = requests.post(f"{BASE_URL}/retrieve_cards", json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_associate_card()
    test_retrieve_cards()