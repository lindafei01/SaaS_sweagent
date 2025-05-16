
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import UserProfile
import json

@csrf_exempt
@require_http_methods(["POST"])
def add_profile(request):
    try:
        # Check if all required fields are present
        if 'username' not in request.POST or 'profile_page' not in request.POST or 'profile_photo' not in request.FILES:
            return HttpResponseBadRequest("Missing required fields")
        
        username = request.POST['username']
        profile_page = request.POST['profile_page']
        profile_photo = request.FILES['profile_photo']
        
        # Check if profile already exists
        if UserProfile.objects.filter(username=username).exists():
            return HttpResponseForbidden("Profile already exists")
        
        # Validate profile photo is PNG
        if not profile_photo.content_type == 'image/png':
            return HttpResponseBadRequest("Profile photo must be PNG format")
        
        # Read the photo data
        photo_data = profile_photo.read()
        
        # Create new profile
        profile = UserProfile(
            username=username,
            profile_page=profile_page,
            profile_photo=photo_data
        )
        profile.save()
        
        return HttpResponse(status=201)
    except Exception as e:
        return HttpResponseBadRequest(str(e))

@require_http_methods(["GET"])
def get_profile(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    return HttpResponse(profile.profile_page, content_type='text/html')

@require_http_methods(["GET"])
def get_profile_photo(request, username):
    profile = get_object_or_404(UserProfile, username=username)
    return HttpResponse(profile.profile_photo, content_type='image/png')