
from django.test import TestCase, Client
from django.urls import reverse
import json
import uuid
from .models import Entry, Edit

class EntryModelTest(TestCase):
    def setUp(self):
        self.entry = Entry.objects.create(
            title="Test Entry",
            content="This is a test entry content.",
            created_by="test_user",
            last_modified_by="test_user"
        )

    def test_entry_creation(self):
        self.assertEqual(self.entry.title, "Test Entry")
        self.assertEqual(self.entry.content, "This is a test entry content.")
        self.assertEqual(self.entry.created_by, "test_user")
        self.assertEqual(self.entry.last_modified_by, "test_user")

class EditModelTest(TestCase):
    def setUp(self):
        self.entry = Entry.objects.create(
            title="Test Entry",
            content="This is a test entry content.",
            created_by="test_user",
            last_modified_by="test_user"
        )
        self.edit = Edit.objects.create(
            entry=self.entry,
            content="Previous content",
            modified_by="editor_user",
            summary="Test edit"
        )

    def test_edit_creation(self):
        self.assertEqual(self.edit.entry, self.entry)
        self.assertEqual(self.edit.content, "Previous content")
        self.assertEqual(self.edit.modified_by, "editor_user")
        self.assertEqual(self.edit.summary, "Test edit")

class APITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.entry = Entry.objects.create(
            title="Test Entry",
            content="This is a test entry content.",
            created_by="test_user",
            last_modified_by="test_user"
        )

    def test_entries_list_get(self):
        response = self.client.get('/entries')
        self.assertEqual(response.status_code, 200)

    def test_entry_creation(self):
        data = {
            "title": "New Entry",
            "content": "This is a new entry content.",
            "createdBy": "api_user"
        }
        response = self.client.post(
            '/entries',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['title'], "New Entry")
        self.assertEqual(response_data['content'], "This is a new entry content.")
        self.assertEqual(response_data['lastModifiedBy'], "api_user")

    def test_entry_detail_get(self):
        response = self.client.get(f'/entries/{self.entry.id}')
        self.assertEqual(response.status_code, 200)

    def test_entry_update(self):
        data = {
            "content": "Updated content",
            "modifiedBy": "editor_user",
            "summary": "Test update"
        }
        response = self.client.put(
            f'/entries/{self.entry.id}',
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['content'], "Updated content")
        self.assertEqual(response_data['lastModifiedBy'], "editor_user")

    def test_entry_edits(self):
        # Create an edit first
        Edit.objects.create(
            entry=self.entry,
            content="Previous content",
            modified_by="editor_user",
            summary="Test edit"
        )
        response = self.client.get(f'/entries/{self.entry.id}/edits')
        self.assertEqual(response.status_code, 200)