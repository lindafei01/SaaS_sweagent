
#!/usr/bin/env python
"""
Simple test script to create sample PDFs and test the concatenation API.
"""
import os
import requests
import tempfile

# Create two simple PDF files
def create_sample_pdf(filename, content="Sample PDF content"):
    with open(filename, 'w') as f:
        f.write("%PDF-1.4\n")
        f.write(content + "\n")
        f.write("%EOF\n")

# Create temporary PDF files
temp_dir = tempfile.mkdtemp()
file1_path = os.path.join(temp_dir, 'file1.pdf')
file2_path = os.path.join(temp_dir, 'file2.pdf')

create_sample_pdf(file1_path, "Content of first PDF")
create_sample_pdf(file2_path, "Content of second PDF")

print(f"Created sample PDFs at {file1_path} and {file2_path}")

# Test the API
try:
    with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2:
        files = [
            ('files', ('file1.pdf', file1, 'application/pdf')),
            ('files', ('file2.pdf', file2, 'application/pdf'))
        ]
        
        response = requests.post('http://0.0.0.0:5000/concatenate', files=files)
        
        if response.status_code == 200:
            # Save the concatenated PDF
            output_path = os.path.join(temp_dir, 'concatenated.pdf')
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"Success! Concatenated PDF saved to {output_path}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
except Exception as e:
    print(f"Error: {str(e)}")

# Clean up
print("Cleaning up temporary files...")
for file_path in [file1_path, file2_path]:
    if os.path.exists(file_path):
        os.unlink(file_path)
if os.path.exists(temp_dir):
    os.rmdir(temp_dir)