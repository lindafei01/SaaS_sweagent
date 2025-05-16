
#!/usr/bin/env python
import os
import sys
import subprocess

def main():
    # Make migrations
    subprocess.run([sys.executable, 'manage.py', 'makemigrations'])
    
    # Apply migrations
    subprocess.run([sys.executable, 'manage.py', 'migrate'])
    
    # Run server
    subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:5000'])

if __name__ == '__main__':
    main()