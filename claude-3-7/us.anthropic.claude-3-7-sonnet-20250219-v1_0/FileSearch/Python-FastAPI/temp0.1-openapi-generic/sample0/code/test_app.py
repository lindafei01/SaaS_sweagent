
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_search_by_content():
    response = client.post(
        "/search",
        json={"search_content": "Hello World"}
    )
    assert response.status_code == 200
    data = response.json()
    print("Search by content response:", data)
    assert "files" in data

def test_search_by_filename():
    response = client.post(
        "/search",
        json={"search_filename": "file"}
    )
    assert response.status_code == 200
    data = response.json()
    print("Search by filename response:", data)
    assert "files" in data

def test_search_with_directory():
    response = client.post(
        "/search",
        json={"search_content": "Hello", "search_dir": "/songs"}
    )
    assert response.status_code == 200
    data = response.json()
    print("Search with directory response:", data)
    assert "files" in data

def test_invalid_request():
    response = client.post(
        "/search",
        json={}
    )
    assert response.status_code == 400
    print("Invalid request response:", response.json())

if __name__ == "__main__":
    # Create test files
    import os
    os.makedirs("/data/files", exist_ok=True)
    os.makedirs("/data/songs", exist_ok=True)
    
    with open("/data/files/file1.txt", "w") as f:
        f.write("Hello World")
    
    with open("/data/files/file2.txt", "w") as f:
        f.write("This is a test")
    
    with open("/data/songs/song.mp3", "w") as f:
        f.write("Hello World song")
    
    print("Running tests...")
    test_search_by_content()
    test_search_by_filename()
    test_search_with_directory()
    test_invalid_request()
    print("All tests passed!")