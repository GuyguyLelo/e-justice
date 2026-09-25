from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import DetectionFaciale

@login_required
def detection_detail_view(request, detection_id):
    """Affiche les détails d'une détection faciale"""
    detection = get_object_or_404(DetectionFaciale, id=detection_id)
    
    context = {
        'detection': detection,
        'page_title': f'Détection #{detection.id}'
    }
    
    return render(request, 'surveillance/detection_detail.html', context)
