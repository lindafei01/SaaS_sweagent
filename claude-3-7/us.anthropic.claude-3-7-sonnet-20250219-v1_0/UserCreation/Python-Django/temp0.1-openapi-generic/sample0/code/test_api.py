
import requests
import json

BASE_URL = 'http://localhost:5000'

def test_invite_user():
    print("Testing invite_user endpoint...")
    response = requests.post(
        f'{BASE_URL}/invite_user',
        json={'email': 'test@example.com'}
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json().get('invite_id')

def test_create_user(invite_id):
    print("\nTesting create_user endpoint...")
    response = requests.post(
        f'{BASE_URL}/create_user',
        json={
            'invite_id': invite_id,
            'user_name': 'testuser',
            'password': 'testpassword'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test duplicate username
    print("\nTesting duplicate username...")
    invite_id = test_invite_user()
    response = requests.post(
        f'{BASE_URL}/create_user',
        json={
            'invite_id': invite_id,
            'user_name': 'testuser',  # Already exists
            'password': 'testpassword'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test invalid invite_id
    print("\nTesting invalid invite_id...")
    response = requests.post(
        f'{BASE_URL}/create_user',
        json={
            'invite_id': '00000000-0000-0000-0000-000000000000',
            'user_name': 'anotheruser',
            'password': 'testpassword'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == '__main__':
    invite_id = test_invite_user()
    if invite_id:
        test_create_user(invite_id)