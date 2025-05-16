
import unittest
import json
import os
from app import app

class WikiAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Remove test database if it exists
        if os.path.exists('db.sqlite3'):
            os.remove('db.sqlite3')
        # Initialize the database
        from app import init_db
        init_db()

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Wiki', response.data)

    def test_entries_list(self):
        response = self.app.get('/entries')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Wiki Entries', response.data)

    def test_create_and_get_entry(self):
        # Create a new entry
        new_entry = {
            'title': 'Test Entry',
            'content': 'This is a test entry content.',
            'createdBy': 'Test User'
        }
        response = self.app.post('/entries', 
                                data=json.dumps(new_entry),
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # Parse the response
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Test Entry')
        self.assertEqual(data['content'], 'This is a test entry content.')
        self.assertEqual(data['lastModifiedBy'], 'Test User')
        
        # Get the entry
        entry_id = data['id']
        response = self.app.get(f'/entries/{entry_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Entry', response.data)
        self.assertIn(b'This is a test entry content.', response.data)

    def test_update_entry(self):
        # First create an entry
        new_entry = {
            'title': 'Entry to Update',
            'content': 'Original content.',
            'createdBy': 'Original Author'
        }
        response = self.app.post('/entries', 
                                data=json.dumps(new_entry),
                                content_type='application/json')
        data = json.loads(response.data)
        entry_id = data['id']
        
        # Now update it
        update_data = {
            'content': 'Updated content.',
            'modifiedBy': 'Editor',
            'summary': 'Updated the content'
        }
        response = self.app.put(f'/entries/{entry_id}',
                               data=json.dumps(update_data),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check the updated entry
        updated_data = json.loads(response.data)
        self.assertEqual(updated_data['content'], 'Updated content.')
        self.assertEqual(updated_data['lastModifiedBy'], 'Editor')
        
        # Check edit history
        response = self.app.get(f'/entries/{entry_id}/edits')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Updated the content', response.data)

    def test_nonexistent_entry(self):
        response = self.app.get('/entries/nonexistent-id')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
import unittest
import json
import os
from app import app

class WikiAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Remove test database if it exists
        if os.path.exists('db.sqlite3'):
            os.remove('db.sqlite3')
        # Initialize the database
        from app import init_db
        init_db()

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to the Wiki', response.data)

    def test_entries_list(self):
        response = self.app.get('/entries')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Wiki Entries', response.data)

    def test_create_and_get_entry(self):
        # Create a new entry
        new_entry = {
            'title': 'Test Entry',
            'content': 'This is a test entry content.',
            'createdBy': 'Test User'
        }
        response = self.app.post('/entries', 
                                data=json.dumps(new_entry),
                                content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        # Parse the response
        data = json.loads(response.data)
        self.assertEqual(data['title'], 'Test Entry')
        self.assertEqual(data['content'], 'This is a test entry content.')
        self.assertEqual(data['lastModifiedBy'], 'Test User')
        
        # Get the entry
        entry_id = data['id']
        response = self.app.get(f'/entries/{entry_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Entry', response.data)
        self.assertIn(b'This is a test entry content.', response.data)

    def test_update_entry(self):
        # First create an entry
        new_entry = {
            'title': 'Entry to Update',
            'content': 'Original content.',
            'createdBy': 'Original Author'
        }
        response = self.app.post('/entries', 
                                data=json.dumps(new_entry),
                                content_type='application/json')
        data = json.loads(response.data)
        entry_id = data['id']
        
        # Now update it
        update_data = {
            'content': 'Updated content.',
            'modifiedBy': 'Editor',
            'summary': 'Updated the content'
        }
        response = self.app.put(f'/entries/{entry_id}',
                               data=json.dumps(update_data),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check the updated entry
        updated_data = json.loads(response.data)
        self.assertEqual(updated_data['content'], 'Updated content.')
        self.assertEqual(updated_data['lastModifiedBy'], 'Editor')
        
        # Check edit history
        response = self.app.get(f'/entries/{entry_id}/edits')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Updated the content', response.data)

    def test_nonexistent_entry(self):
        response = self.app.get('/entries/nonexistent-id')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()