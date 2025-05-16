
from PIL import Image
import os

# Create a directory for test images
os.makedirs("test_images", exist_ok=True)

# Create 3 simple test images with different colors
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue

for i, color in enumerate(colors):
    img = Image.new('RGB', (100, 100), color)
    path = f"test_images/test_image_{i}.png"
    img.save(path)
    print(f"Created {path}")

print("Test images created successfully!")