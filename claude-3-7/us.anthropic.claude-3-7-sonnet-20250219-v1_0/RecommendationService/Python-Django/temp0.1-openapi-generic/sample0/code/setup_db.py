
import os
import django
import subprocess

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Run migrations
print("Running migrations...")
subprocess.run(['python', 'manage.py', 'makemigrations', 'myapp'])
subprocess.run(['python', 'manage.py', 'migrate'])

print("Database setup complete!")

# Create some sample data
from myapp.models import Product, Tag

def create_sample_data():
    print("Creating sample data...")
    
    # Create products
    product1 = Product.objects.create(name="Smartphone")
    product2 = Product.objects.create(name="Laptop")
    product3 = Product.objects.create(name="Headphones")
    product4 = Product.objects.create(name="Smartwatch")
    
    # Create tags
    tag_electronics = Tag.objects.create(name="electronics")
    tag_mobile = Tag.objects.create(name="mobile")
    tag_audio = Tag.objects.create(name="audio")
    tag_wearable = Tag.objects.create(name="wearable")
    tag_computing = Tag.objects.create(name="computing")
    
    # Associate tags with products
    tag_electronics.products.add(product1, product2, product3, product4)
    tag_mobile.products.add(product1, product4)
    tag_audio.products.add(product3)
    tag_wearable.products.add(product4)
    tag_computing.products.add(product2)
    
    print("Sample data created successfully!")

# Check if there's any existing data
if not Product.objects.exists():
    create_sample_data()
else:
    print("Sample data already exists, skipping creation.")