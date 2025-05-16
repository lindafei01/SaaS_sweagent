
import requests
import os

# URL of the API endpoint
url = "http://0.0.0.0:5000/concatenate"

# Files to upload
files = [
    ("files", ("test1.pdf", open("test1.pdf", "rb"), "application/pdf")),
    ("files", ("test2.pdf", open("test2.pdf", "rb"), "application/pdf"))
]

try:
    # Send POST request to the API
    response = requests.post(url, files=files)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Save the concatenated PDF
        with open("concatenated_result.pdf", "wb") as f:
            f.write(response.content)
        print("Concatenated PDF saved as concatenated_result.pdf")
        
        # Verify the file exists and has content
        if os.path.exists("concatenated_result.pdf") and os.path.getsize("concatenated_result.pdf") > 0:
            print("Verification successful: File exists and has content")
        else:
            print("Verification failed: File does not exist or is empty")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"An error occurred: {str(e)}")
    
# Close the file handles
for _, file_tuple in files:
    file_tuple[1].close()