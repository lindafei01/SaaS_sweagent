
import requests
import json
import time
import subprocess
import os
import signal
import sys

# Start the FastAPI server in the background
print("Starting the FastAPI server...")
server_process = subprocess.Popen(["python", "app.py"])

# Wait for the server to start
time.sleep(2)

BASE_URL = "http://0.0.0.0:5000"

def test_add_product():
    print("\nTesting /add endpoint...")
    # Test adding a product with additional properties
    product_data = {
        "name": "Test Product",
        "category": "Electronics",
        "price": "99.99",
        "in_stock": "true"
    }
    
    response = requests.post(f"{BASE_URL}/add", json=product_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201, "Failed to add product"

def test_download_product():
    print("\nTesting /download endpoint...")
    # Test downloading a product
    response = requests.get(f"{BASE_URL}/download?name=Test Product")
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, "Failed to download product"
    
    # Verify the data contains all properties
    data = json.loads(response.json()["data"])
    assert data["name"] == "Test Product", "Name mismatch"
    assert data["category"] == "Electronics", "Category mismatch"
    assert data["price"] == "99.99", "Price mismatch"
    assert data["in_stock"] == "true", "In stock mismatch"

def test_upload_product():
    print("\nTesting /upload endpoint...")
    # Test uploading updated product data
    product_data = {
        "name": "Test Product",
        "category": "Electronics",
        "price": "89.99",  # Updated price
        "in_stock": "true",
        "color": "black"   # New property
    }
    
    upload_data = {
        "name": "Test Product",
        "data": json.dumps(product_data)
    }
    
    response = requests.post(f"{BASE_URL}/upload", json=upload_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, "Failed to upload product"
    
    # Verify the update by downloading the product again
    response = requests.get(f"{BASE_URL}/download?name=Test Product")
    data = json.loads(response.json()["data"])
    assert data["price"] == "89.99", "Price not updated"
    assert data["color"] == "black", "New property not added"

def test_search_products():
    print("\nTesting /search endpoint...")
    # Add another product for search testing
    product_data = {
        "name": "Another Product",
        "category": "Clothing",
        "price": "49.99"
    }
    
    requests.post(f"{BASE_URL}/add", json=product_data)
    
    # Test searching by name
    response = requests.get(f"{BASE_URL}/search?query=Test")
    print(f"Search by name - Status code: {response.status_code}")
    print(f"Search by name - Results count: {len(response.json()['results'])}")
    
    assert response.status_code == 200, "Search failed"
    assert len(response.json()["results"]) >= 1, "Search by name returned no results"
    
    # Test searching by property value
    response = requests.get(f"{BASE_URL}/search?query=Electronics")
    print(f"Search by property - Status code: {response.status_code}")
    print(f"Search by property - Results count: {len(response.json()['results'])}")
    
    assert response.status_code == 200, "Search failed"
    assert len(response.json()["results"]) >= 1, "Search by property returned no results"

def run_tests():
    try:
        test_add_product()
        test_download_product()
        test_upload_product()
        test_search_products()
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nError during testing: {e}")
    finally:
        # Stop the server
        print("\nStopping the server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\nTests interrupted. Stopping the server...")
        server_process.terminate()
        server_process.wait()
        sys.exit(1)