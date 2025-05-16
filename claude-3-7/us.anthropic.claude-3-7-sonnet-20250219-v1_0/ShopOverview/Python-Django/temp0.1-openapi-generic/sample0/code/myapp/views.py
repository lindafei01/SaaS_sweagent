
import json
import csv
import io
import jwt
import datetime
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from .models import Merchant, Ware

# Authentication middleware
def get_merchant_from_token(request):
    auth_cookie = request.COOKIES.get('AUTH_COOKIE')
    if not auth_cookie:
        return None
    
    try:
        payload = jwt.decode(auth_cookie, settings.SECRET_KEY, algorithms=['HS256'])
        merchant = Merchant.objects.get(id=payload['merchant_id'])
        return merchant
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Merchant.DoesNotExist):
        return None

@csrf_exempt
@require_http_methods(["POST"])
def register_merchant(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        name = data.get('name')
        password = data.get('password')
        
        if not all([email, name, password]):
            return JsonResponse({'error': 'Email, name, and password are required'}, status=400)
        
        # Check if merchant with this email already exists
        if Merchant.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Merchant with this email already exists'}, status=400)
        
        # Create new merchant with hashed password
        merchant = Merchant.objects.create(
            email=email,
            name=name,
            password=make_password(password)
        )
        
        return JsonResponse({'message': 'Merchant registered successfully'}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def login_merchant(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        try:
            merchant = Merchant.objects.get(email=email)
        except Merchant.DoesNotExist:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)
        
        if not check_password(password, merchant.password):
            return JsonResponse({'error': 'Invalid email or password'}, status=401)
        
        # Generate JWT token
        payload = {
            'merchant_id': merchant.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        
        response = JsonResponse({'message': 'Login successful'})
        response.set_cookie('AUTH_COOKIE', token, httponly=True, secure=True, samesite='Strict')
        return response
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def upload_wares(request):
    merchant = get_merchant_from_token(request)
    if not merchant:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        data = json.loads(request.body)
        csv_data = data.get('csv')
        
        if not csv_data:
            return JsonResponse({'error': 'CSV data is required'}, status=400)
        
        # Parse CSV data
        csv_file = io.StringIO(csv_data)
        reader = csv.reader(csv_file)
        
        wares_created = 0
        for row in reader:
            if len(row) != 3:
                continue
                
            name, description, price = row
            
            try:
                price = Decimal(price)
                if price <= 0:
                    continue
            except:
                continue
                
            Ware.objects.create(
                merchant=merchant,
                name=name,
                description=description,
                price=price
            )
            wares_created += 1
        
        return JsonResponse({'message': f'{wares_created} wares uploaded successfully'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@require_http_methods(["GET"])
def list_wares(request):
    # Get filter parameters
    min_price = request.GET.get('minPrice')
    max_price = request.GET.get('maxPrice')
    
    # Start with all wares
    wares = Ware.objects.all()
    
    # Apply filters if provided
    if min_price:
        try:
            min_price = Decimal(min_price)
            wares = wares.filter(price__gte=min_price)
        except:
            pass
            
    if max_price:
        try:
            max_price = Decimal(max_price)
            wares = wares.filter(price__lte=max_price)
        except:
            pass
    
    # Generate HTML table
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Available Wares</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Available Wares</h1>
        <table>
            <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Price</th>
                <th>Merchant</th>
            </tr>
    """
    
    for ware in wares:
        html += f"""
            <tr>
                <td>{ware.name}</td>
                <td>{ware.description}</td>
                <td>${ware.price}</td>
                <td>{ware.merchant.email}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return HttpResponse(html)