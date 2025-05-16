
import json
from fastapi.testclient import TestClient
from app import app

# Create test client
client = TestClient(app)

def test_add_product():
    print("\nTesting /add endpoint...")
    # Test adding a product with additional properties
    product_data = {
        "name": "Test Product",
        "category": "Electronics",
        "price": "99.99",
        "in_stock": "true"
    }
    
    response = client.post("/add", json=product_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 201, "Failed to add product"

def test_download_product():
    print("\nTesting /download endpoint...")
    # Test downloading a product
    response = client.get("/download?name=Test%20Product")
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
    
    response = client.post("/upload", json=upload_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200, "Failed to upload product"
    
    # Verify the update by downloading the product again
    response = client.get("/download?name=Test%20Product")
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
    
    client.post("/add", json=product_data)
    
    # Test searching by name
    response = client.get("/search?query=Test")
    print(f"Search by name - Status code: {response.status_code}")
    print(f"Search by name - Results count: {len(response.json()['results'])}")
    
    assert response.status_code == 200, "Search failed"
    assert len(response.json()["results"]) >= 1, "Search by name returned no results"
    
    # Test searching by property value
    response = client.get("/search?query=Electronics")
    print(f"Search by property - Status code: {response.status_code}")
    print(f"Search by property - Results count: {len(response.json()['results'])}")
    
    assert response.status_code == 200, "Search failed"
    assert len(response.json()["results"]) >= 1, "Search by property returned no results"

def run_tests():
    try:
        # Remove the database file if it exists
        import os
        if os.path.exists("db.sqlite3"):
            os.remove("db.sqlite3")
            
        test_add_product()
        test_download_product()
        test_upload_product()
        test_search_products()
        print("\nAll tests passed successfully!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nError during testing: {e}")

if __name__ == "__main__":
    run_tests()