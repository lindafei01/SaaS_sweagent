
import requests
import json

def test_compile_endpoint():
    print("Testing /compile endpoint...")
    
    # Test TypeScript with error
    print("\nTesting TypeScript with error:")
    response = requests.post(
        'http://localhost:5000/compile',
        json={
            'fileName': 'test.ts',
            'fileContent': 'let x = y * 2;'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test TypeScript without error
    print("\nTesting TypeScript without error:")
    response = requests.post(
        'http://localhost:5000/compile',
        json={
            'fileName': 'test.ts',
            'fileContent': 'let x = 2 * 15;'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test C++ with error
    print("\nTesting C++ with error:")
    response = requests.post(
        'http://localhost:5000/compile',
        json={
            'fileName': 'test.cpp',
            'fileContent': 'int main() { undefinedVar = 10; return 0; }'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test C++ without error
    print("\nTesting C++ without error:")
    response = requests.post(
        'http://localhost:5000/compile',
        json={
            'fileName': 'test.cpp',
            'fileContent': 'int main() { return 0; }'
        }
    )
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_compile_endpoint()