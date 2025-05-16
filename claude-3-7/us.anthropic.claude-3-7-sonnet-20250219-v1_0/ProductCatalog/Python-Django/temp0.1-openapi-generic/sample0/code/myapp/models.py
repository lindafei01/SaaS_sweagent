
from django.db import models
import json

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    properties = models.TextField(default='{}')  # Store additional properties as JSON
    
    def set_properties(self, props_dict):
        """Set additional properties as JSON"""
        # Ensure name is not in properties to avoid duplication
        if 'name' in props_dict:
            del props_dict['name']
        self.properties = json.dumps(props_dict)
    
    def get_properties(self):
        """Get additional properties as dict"""
        return json.loads(self.properties)
    
    def to_dict(self):
        """Convert product to dictionary including all properties"""
        result = {'name': self.name}
        result.update(self.get_properties())
        return result
    
    def __str__(self):
        return self.name