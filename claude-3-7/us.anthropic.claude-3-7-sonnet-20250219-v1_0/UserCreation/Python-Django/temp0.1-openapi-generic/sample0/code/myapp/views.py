
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import Invitation

@csrf_exempt
def invite_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({'message': 'Email is required'}, status=400)
            
            # Check if invitation already exists
            invitation, created = Invitation.objects.get_or_create(
                email=email,
                defaults={'created_by': None}
            )
            
            return JsonResponse({
                'invite_id': str(invitation.invite_id),
                'message': 'Invitation created successfully' if created else 'Invitation already exists'
            })
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)
    
    return JsonResponse({'message': 'Method not allowed'}, status=405)

@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invite_id = data.get('invite_id')
            user_name = data.get('user_name')
            password = data.get('password')
            
            if not all([invite_id, user_name, password]):
                return JsonResponse({'message': 'All fields are required'}, status=400)
            
            # Check if invitation exists and is valid
            try:
                invitation = Invitation.objects.get(invite_id=invite_id, is_used=False)
            except Invitation.DoesNotExist:
                return JsonResponse({'message': 'Invalid invite_id'}, status=401)
            
            # Create user
            try:
                user = User.objects.create_user(username=user_name, email=invitation.email, password=password)
                
                # Mark invitation as used
                invitation.is_used = True
                invitation.save()
                
                return JsonResponse({'message': 'User created successfully'})
            except IntegrityError:
                return JsonResponse({'message': 'Username already exists. Try providing different username.'}, status=400)
            
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=400)
    
    return JsonResponse({'message': 'Method not allowed'}, status=405)