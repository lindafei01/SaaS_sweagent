
import json
import jwt
import os
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import IntegrityError
from .models import Secret

# Get the secret key from environment variable or use a default one
SECRET_KEY = os.environ.get('APP_SECRET', 'django-insecure-default-key-for-development')

def generate_token(user_id):
    """Generate JWT token for authentication"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(request):
    """Verify JWT token from request headers"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        return User.objects.filter(id=user_id).first()
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@csrf_exempt
def register(request):
    """Register a new user with email, username and password"""
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        # Validate input
        if not all([email, username, password]):
            return JsonResponse({'message': 'Email, username and password are required'}, status=400)
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        return JsonResponse({'message': 'Registration successful'}, status=201)
    
    except IntegrityError:
        return JsonResponse({'message': 'Email already in use or invalid data'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)

@csrf_exempt
def login(request):
    """Authenticate a user with email and password"""
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not all([email, password]):
            return JsonResponse({'message': 'Email and password are required'}, status=400)
        
        # Find user by email
        user = User.objects.filter(email=email).first()
        if not user or not authenticate(username=user.username, password=password):
            return JsonResponse({'message': 'Invalid email or password'}, status=401)
        
        # Generate token
        token = generate_token(user.id)
        return JsonResponse({
            'token': token,
            'message': 'Login successful'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)

@csrf_exempt
def set_secret(request):
    """Save a secret on the server"""
    if request.method != 'POST':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    # Verify authentication
    user = verify_token(request)
    if not user:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        secret_text = data.get('secret')
        
        # Validate input
        if not all([username, secret_text]):
            return JsonResponse({'message': 'Username and secret are required'}, status=400)
        
        # Verify that the username matches the authenticated user
        if user.username != username:
            return JsonResponse({'message': 'You can only set secrets for your own account'}, status=403)
        
        # Save or update the secret
        secret, created = Secret.objects.update_or_create(
            user=user,
            defaults={'secret_text': secret_text}
        )
        
        return JsonResponse({'message': 'Secret has been set successfully'})
    
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)

@csrf_exempt
def get_secret(request):
    """Retrieve a secret based on the provided username"""
    if request.method != 'GET':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    # Verify authentication
    user = verify_token(request)
    if not user:
        return JsonResponse({'message': 'Invalid authentication token'}, status=401)
    
    username = request.GET.get('username')
    if not username:
        return JsonResponse({'message': 'Username is required'}, status=400)
    
    # Find the user by username
    target_user = User.objects.filter(username=username).first()
    if not target_user:
        return JsonResponse({'message': 'User not found'}, status=404)
    
    # Get the secret
    secret = Secret.objects.filter(user=target_user).first()
    if not secret:
        return JsonResponse({'message': 'No secret found for this user'}, status=404)
    
    return JsonResponse({'secret': secret.secret_text})