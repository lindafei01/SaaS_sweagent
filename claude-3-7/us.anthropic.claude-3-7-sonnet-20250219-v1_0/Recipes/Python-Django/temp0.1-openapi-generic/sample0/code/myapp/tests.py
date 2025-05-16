
import json
import uuid
from django.test import TestCase, Client
from django.urls import reverse
from .models import Recipe, Comment, Rating

class RecipeAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.recipe = Recipe.objects.create(
            title="Test Recipe",
            ingredients=["Ingredient 1", "Ingredient 2"],
            instructions="Test instructions"
        )
    
    def test_recipes_overview(self):
        response = self.client.get(reverse('recipes_overview'))
        self.assertEqual(response.status_code, 200)
    
    def test_upload_recipe(self):
        data = {
            "title": "New Recipe",
            "ingredients": ["Ingredient 1", "Ingredient 2"],
            "instructions": "New instructions"
        }
        response = self.client.post(
            reverse('upload_recipe'),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Recipe.objects.filter(title="New Recipe").exists())
    
    def test_get_recipe(self):
        response = self.client.get(reverse('get_recipe', args=[str(self.recipe.id)]))
        self.assertEqual(response.status_code, 200)
    
    def test_add_comment(self):
        data = {"comment": "Test comment"}
        response = self.client.post(
            reverse('add_comment', args=[str(self.recipe.id)]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Comment.objects.filter(recipe=self.recipe).exists())
    
    def test_add_rating(self):
        data = {"rating": 5}
        response = self.client.post(
            reverse('add_rating', args=[str(self.recipe.id)]),
            json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Rating.objects.filter(recipe=self.recipe).exists())
    
    def test_invalid_recipe_id(self):
        invalid_id = uuid.uuid4()
        response = self.client.get(reverse('get_recipe', args=[str(invalid_id)]))
        self.assertEqual(response.status_code, 404)