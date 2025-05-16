
import requests
import json
import time

BASE_URL = "http://0.0.0.0:5000"

def test_recipe_upload():
    print("Testing recipe upload...")
    
    # Test data
    recipe_data = {
        "title": "Test Spaghetti Carbonara",
        "ingredients": ["Spaghetti", "Eggs", "Pancetta", "Parmesan Cheese"],
        "instructions": "Boil pasta. Cook pancetta. Mix eggs and cheese. Combine all."
    }
    
    try:
        # Upload recipe with timeout
        response = requests.post(f"{BASE_URL}/recipes/upload", json=recipe_data, timeout=5)
        
        if response.status_code == 201:
            print("Recipe uploaded successfully!")
            recipe = response.json()
            print(f"Recipe ID: {recipe['id']}")
            return recipe['id']
        else:
            print(f"Failed to upload recipe. Status code: {response.status_code}")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_add_comment(recipe_id):
    print("\nTesting adding a comment...")
    
    # Test data
    comment_data = {
        "comment": "This recipe is amazing!"
    }
    
    try:
        # Add comment with timeout
        response = requests.post(f"{BASE_URL}/recipes/{recipe_id}/comments", json=comment_data, timeout=5)
        
        if response.status_code == 201:
            print("Comment added successfully!")
        else:
            print(f"Failed to add comment. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_add_rating(recipe_id):
    print("\nTesting adding a rating...")
    
    # Test data
    rating_data = {
        "rating": 5
    }
    
    try:
        # Add rating with timeout
        response = requests.post(f"{BASE_URL}/recipes/{recipe_id}/ratings", json=rating_data, timeout=5)
        
        if response.status_code == 201:
            print("Rating added successfully!")
        else:
            print(f"Failed to add rating. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_get_recipe(recipe_id):
    print("\nTesting getting a recipe...")
    
    try:
        # Get recipe with timeout
        response = requests.get(f"{BASE_URL}/recipes/{recipe_id}", timeout=5)
        
        if response.status_code == 200:
            print("Recipe retrieved successfully!")
            print("HTML content received.")
        else:
            print(f"Failed to get recipe. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def test_get_recipes():
    print("\nTesting getting recipe overview...")
    
    try:
        # Get recipes with timeout
        response = requests.get(f"{BASE_URL}/recipes", timeout=5)
        
        if response.status_code == 200:
            print("Recipe overview retrieved successfully!")
            print("HTML content received.")
        else:
            print(f"Failed to get recipe overview. Status code: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def run_tests():
    print("Starting API tests...")
    
    # Wait for the server to start
    time.sleep(1)
    
    # Upload a recipe
    recipe_id = test_recipe_upload()
    
    if recipe_id:
        # Add a comment
        test_add_comment(recipe_id)
        
        # Add a rating
        test_add_rating(recipe_id)
        
        # Get the recipe
        test_get_recipe(recipe_id)
    
    # Get recipe overview
    test_get_recipes()
    
    print("\nTests completed!")

if __name__ == "__main__":
    run_tests()