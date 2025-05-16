
import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import difflib

from .models import Entry, Edit

@csrf_exempt
def entries_list(request):
    """Get a list of all entries with their titles and links"""
    if request.method == 'GET':
        entries = Entry.objects.all().order_by('title')
        return render(request, 'myapp/entries_list.html', {'entries': entries})
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            content = data.get('content')
            created_by = data.get('createdBy')
            
            if not all([title, content, created_by]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            entry = Entry.objects.create(
                title=title,
                content=content,
                created_by=created_by,
                last_modified_by=created_by
            )
            
            return JsonResponse({
                'id': str(entry.id),
                'title': entry.title,
                'content': entry.content,
                'lastModifiedBy': entry.last_modified_by,
                'lastModifiedAt': entry.last_modified_at.isoformat()
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

@csrf_exempt
@require_http_methods(["GET", "PUT"])
def entry_detail(request, entry_id):
    """Get or update a specific entry"""
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        raise Http404("Entry not found")
    
    if request.method == 'GET':
        # Get all unique contributors
        contributors = set([entry.created_by])
        for edit in entry.edits.all():
            contributors.add(edit.modified_by)
        
        return render(request, 'myapp/entry_detail.html', {
            'entry': entry,
            'contributors': list(contributors)
        })
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            content = data.get('content')
            modified_by = data.get('modifiedBy')
            summary = data.get('summary', '')
            
            if not all([content, modified_by]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            # Create an edit record
            Edit.objects.create(
                entry=entry,
                content=entry.content,  # Store the previous content
                modified_by=modified_by,
                summary=summary
            )
            
            # Update the entry
            entry.content = content
            entry.last_modified_by = modified_by
            entry.last_modified_at = timezone.now()
            entry.save()
            
            return JsonResponse({
                'id': str(entry.id),
                'title': entry.title,
                'content': entry.content,
                'lastModifiedBy': entry.last_modified_by,
                'lastModifiedAt': entry.last_modified_at.isoformat()
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

def entry_edits(request, entry_id):
    """View the history of edits for a specific entry"""
    try:
        entry = Entry.objects.get(id=entry_id)
    except Entry.DoesNotExist:
        raise Http404("Entry not found")
    
    edits = entry.edits.all().order_by('-modified_at')
    
    # Calculate diffs for each edit
    edit_history = []
    current_content = entry.content
    
    for edit in edits:
        diff = difflib.unified_diff(
            edit.content.splitlines(),
            current_content.splitlines(),
            lineterm='',
            n=3
        )
        
        edit_history.append({
            'edit': edit,
            'diff': '\n'.join(diff)
        })
        
        current_content = edit.content
    
    return render(request, 'myapp/entry_edits.html', {
        'entry': entry,
        'edit_history': edit_history
    })