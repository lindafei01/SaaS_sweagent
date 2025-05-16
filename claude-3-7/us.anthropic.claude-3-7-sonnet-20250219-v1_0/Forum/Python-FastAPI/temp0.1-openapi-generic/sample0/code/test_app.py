
import sqlite3
import json

def test_database_setup():
    # Test that the database was created
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 'messages':
            print("✅ Database setup successful: 'messages' table exists")
        else:
            print("❌ Database setup failed: 'messages' table does not exist")
    except Exception as e:
        print(f"❌ Database setup failed with error: {e}")

def test_app_structure():
    # Test that the app has the required routes and functionality
    from app import app
    
    # Check if the app has the required routes
    routes = [route.path for route in app.routes]
    
    if "/messages" in routes and "/" in routes:
        print("✅ App structure check: Required routes exist")
    else:
        print("❌ App structure check: Missing required routes")
        print(f"Available routes: {routes}")

if __name__ == "__main__":
    print("Running tests for MyForum app...")
    test_database_setup()
    test_app_structure()
    print("Tests completed.")