from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods

from .models import (
    Camera, ZoneSurveillance, ProfilFacialDetenu, 
    DetectionFaciale, AlerteSurveillance, StatutCamera
)
from apps.detenus.models import Detenu, CentrePenitencier
from apps.comptes.models import Utilisateur


@login_required
def surveillance_dashboard(request):
    """Vue principale du dashboard de surveillance"""
    # Statistiques des caméras
    camera_stats = {
        'total': Camera.objects.count(),
        'actives': Camera.objects.filter(statut='ACTIVE').count(),
        'inactives': Camera.objects.filter(statut='INACTIVE').count(),
        'en_maintenance': Camera.objects.filter(statut='MAINTENANCE').count(),
        'hors_service': Camera.objects.filter(statut='HORS_SERVICE').count(),
    }
    
    # Statistiques des détections
    now = timezone.now()
    detection_stats = {
        'total': DetectionFaciale.objects.count(),
        'aujourd_hui': DetectionFaciale.objects.filter(
            timestamp__date=now.date()
        ).count(),
        'cette_semaine': DetectionFaciale.objects.filter(
            timestamp__gte=now - timezone.timedelta(days=7)
        ).count(),
        'identifiees': DetectionFaciale.objects.filter(
            detenu__isnull=False
        ).count(),
        'alertes': DetectionFaciale.objects.filter(est_alerte=True).count(),
    }
    
    # Statistiques des alertes
    alerte_stats = {
        'total': AlerteSurveillance.objects.count(),
        'ouvertes': AlerteSurveillance.objects.filter(
            statut__in=['OUVERTE', 'EN_COURS']
        ).count(),
        'critiques': AlerteSurveillance.objects.filter(
            niveau='CRITIQUE',
            statut__in=['OUVERTE', 'EN_COURS']
        ).count(),
        'aujourd_hui': AlerteSurveillance.objects.filter(
            date_creation__date=now.date()
        ).count(),
    }
    
    # Données récentes
    recentes_detections = DetectionFaciale.objects.select_related(
        'camera', 'detenu'
    ).order_by('-timestamp')[:10]
    
    alertes_actives = AlerteSurveillance.objects.filter(
        statut__in=['OUVERTE', 'EN_COURS']
    ).select_related('camera', 'detenu').order_by('-date_creation')[:10]
    
    # Caméras par centre
    cameras_par_centre = Camera.objects.values('centre__nom').annotate(
        total=Count('id'),
        actives=Count('id', filter=Q(statut='ACTIVE'))
    ).order_by('-total')
    
    context = {
        'camera_stats': camera_stats,
        'detection_stats': detection_stats,
        'alerte_stats': alerte_stats,
        'recentes_detections': recentes_detections,
        'alertes_actives': alertes_actives,
        'cameras_par_centre': cameras_par_centre,
    }
    
    return render(request, 'surveillance/surveillance_dashboard.html', context)


class CameraListView(LoginRequiredMixin, ListView):
    """Liste des caméras de surveillance"""
    model = Camera
    template_name = 'surveillance/camera_list.html'
    context_object_name = 'cameras'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Camera.objects.select_related('centre')
        
        # Filtrage par centre
        centre_id = self.request.GET.get('centre')
        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(code__icontains=search) |
                Q(emplacement__icontains=search)
            )
        
        return queryset.order_by('centre__nom', 'nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['centres'] = CentrePenitencier.objects.all()
        context['statuts'] = StatutCamera.choices
        context['cameras'] = Camera.objects.all()
        context['detenus'] = Detenu.objects.all()
        return context


class CameraDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une caméra"""
    model = Camera
    template_name = 'surveillance/camera_detail.html'
    context_object_name = 'camera'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        camera = self.get_object()
        
        # Zones de surveillance
        context['zones'] = camera.zones.all()
        
        # Détections récentes
        context['recent_detections'] = DetectionFaciale.objects.filter(
            camera=camera
        ).select_related('detenu').order_by('-timestamp')[:20]
        
        # Statistiques des détections
        context['detection_stats'] = {
            'total': DetectionFaciale.objects.filter(camera=camera).count(),
            'aujourd_hui': DetectionFaciale.objects.filter(
                camera=camera,
                timestamp__date=timezone.now().date()
            ).count(),
            'cette_semaine': DetectionFaciale.objects.filter(
                camera=camera,
                timestamp__gte=timezone.now() - timezone.timedelta(days=7)
            ).count(),
        }
        
        return context


class DetectionListView(LoginRequiredMixin, ListView):
    """Liste des détections faciales"""
    model = DetectionFaciale
    template_name = 'surveillance/detection_list.html'
    context_object_name = 'detections'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = DetectionFaciale.objects.select_related(
            'camera', 'camera__centre', 'detenu', 'zone'
        )
        
        # Filtrage par caméra
        camera_id = self.request.GET.get('camera')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        # Filtrage par détenu
        detenu_id = self.request.GET.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        # Filtrage par statut
        traitee = self.request.GET.get('traitee')
        if traitee == 'oui':
            queryset = queryset.filter(traitee=True)
        elif traitee == 'non':
            queryset = queryset.filter(traitee=False)
        
        # Filtrage par alerte
        alerte = self.request.GET.get('alerte')
        if alerte == 'oui':
            queryset = queryset.filter(est_alerte=True)
        elif alerte == 'non':
            queryset = queryset.filter(est_alerte=False)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        if date_debut:
            queryset = queryset.filter(timestamp__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(timestamp__lte=date_fin)
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cameras'] = Camera.objects.select_related('centre').all()
        context['detenus'] = Detenu.objects.all()
        return context


class AlerteListView(LoginRequiredMixin, ListView):
    """Liste des alertes de surveillance"""
    model = AlerteSurveillance
    template_name = 'surveillance/alerte_list.html'
    context_object_name = 'alertes'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = AlerteSurveillance.objects.select_related(
            'camera', 'camera__centre', 'detection', 'detenu',
            'assigne_a', 'traitee_par'
        )
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtrage par niveau
        niveau = self.request.GET.get('niveau')
        if niveau:
            queryset = queryset.filter(niveau=niveau)
        
        # Filtrage par type
        type_alerte = self.request.GET.get('type')
        if type_alerte:
            queryset = queryset.filter(type_alerte=type_alerte)
        
        # Filtrage par utilisateur assigné
        assigne_a = self.request.GET.get('assigne_a')
        if assigne_a:
            queryset = queryset.filter(assigne_a_id=assigne_a)
        
        return queryset.order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuts'] = AlerteSurveillance.STATUT_ALERTE_CHOICES
        context['niveaux'] = AlerteSurveillance.NIVEAU_ALERTE_CHOICES
        context['types'] = AlerteSurveillance.TYPE_ALERTE_CHOICES
        context['utilisateurs'] = Utilisateur.objects.all()
        return context


@login_required
def alerte_detail(request, alerte_id):
    """Détail d'une alerte"""
    alerte = get_object_or_404(
        AlerteSurveillance.objects.select_related(
            'camera', 'detection', 'detenu', 'assigne_a', 'traitee_par'
        ),
        id=alerte_id
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'assigner':
            alerte.assigne_a = request.user
            alerte.statut = 'EN_COURS'
            alerte.save()
            messages.success(request, 'Alerte assignée avec succès')
        
        elif action == 'resoudre':
            alerte.statut = 'RESOLUE'
            alerte.traitee_par = request.user
            alerte.date_traitement = timezone.now()
            alerte.resolution = request.POST.get('resolution', '')
            alerte.save()
            messages.success(request, 'Alerte résolue avec succès')
        
        elif action == 'fausse_alerte':
            alerte.statut = 'FAUSSE_ALERTE'
            alerte.traitee_par = request.user
            alerte.date_traitement = timezone.now()
            alerte.resolution = request.POST.get('resolution', 'Fausse alerte')
            alerte.save()
            messages.success(request, 'Alerte marquée comme fausse alerte')
        
        return redirect('surveillance:alerte_detail', alerte_id=alerte.id)
    
    return render(request, 'surveillance/alerte_detail.html', {'alerte': alerte})


@login_required
def detection_detail(request, detection_id):
    """Détail d'une détection"""
    detection = get_object_or_404(
        DetectionFaciale.objects.select_related(
            'camera', 'camera__centre', 'detenu', 'zone', 'traitee_par'
        ),
        id=detection_id
    )
    
    if request.method == 'POST':
        detection.traitee = True
        detection.traitee_par = request.user
        detection.date_traitement = timezone.now()
        detection.notes = request.POST.get('notes', '')
        detection.save()
        messages.success(request, 'Détection traitée avec succès')
        return redirect('surveillance:detection_detail', detection_id=detection.id)
    
    return render(request, 'surveillance/detection_detail.html', {'detection': detection})


@login_required
def profils_faciaux_list(request):
    """Liste des profils faciaux"""
    profils = ProfilFacialDetenu.objects.select_related('detenu', 'created_by')
    
    # Filtrage
    actif = request.GET.get('actif')
    if actif == 'oui':
        profils = profils.filter(actif=True)
    elif actif == 'non':
        profils = profils.filter(actif=False)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        profils = profils.filter(
            Q(detenu__nom__icontains=search) |
            Q(detenu__prenom__icontains=search) |
            Q(detenu__matricule__icontains=search)
        )
    
    paginator = Paginator(profils.order_by('-date_enregistrement'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'surveillance/profils_faciaux_list.html', {'page_obj': page_obj})


@login_required
def camera_stream(request, camera_id):
    """Vue pour le flux d'une caméra (placeholder)"""
    camera = get_object_or_404(Camera, id=camera_id)
    
    # Dans une implémentation réelle, cette vue servirait le flux vidéo
    # Pour l'instant, elle retourne une page avec un placeholder
    
    return render(request, 'surveillance/camera_stream.html', {'camera': camera})


@login_required
def api_camera_stats(request):
    """API pour les statistiques des caméras"""
    stats = {
        'total': Camera.objects.count(),
        'actives': Camera.objects.filter(statut='ACTIVE').count(),
        'inactives': Camera.objects.filter(statut='INACTIVE').count(),
        'en_maintenance': Camera.objects.filter(statut='MAINTENANCE').count(),
        'hors_service': Camera.objects.filter(statut='HORS_SERVICE').count(),
    }
    
    return JsonResponse(stats)


@login_required
def api_detection_stats(request):
    """API pour les statistiques des détections"""
    now = timezone.now()
    stats = {
        'total': DetectionFaciale.objects.count(),
        'aujourd_hui': DetectionFaciale.objects.filter(
            timestamp__date=now.date()
        ).count(),
        'cette_semaine': DetectionFaciale.objects.filter(
            timestamp__gte=now - timezone.timedelta(days=7)
        ).count(),
        'identifiees': DetectionFaciale.objects.filter(
            detenu__isnull=False
        ).count(),
        'alertes': DetectionFaciale.objects.filter(est_alerte=True).count(),
    }
    
    return JsonResponse(stats)


@login_required
def api_alerte_stats(request):
    """API pour les statistiques des alertes"""
    now = timezone.now()
    stats = {
        'total': AlerteSurveillance.objects.count(),
        'ouvertes': AlerteSurveillance.objects.filter(
            statut__in=['OUVERTE', 'EN_COURS']
        ).count(),
        'critiques': AlerteSurveillance.objects.filter(
            niveau='CRITIQUE',
            statut__in=['OUVERTE', 'EN_COURS']
        ).count(),
        'aujourd_hui': AlerteSurveillance.objects.filter(
            date_creation__date=now.date()
        ).count(),
    }
    
    return JsonResponse(stats)


@login_required
def detections_list(request):
    """Vue pour lister toutes les détections avec filtres"""
    # Récupérer les paramètres de filtre
    search_query = request.GET.get('search', '')
    camera_id = request.GET.get('camera', '')
    detenu_id = request.GET.get('detenu', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    statut = request.GET.get('statut', '')  # 'identifie', 'inconnu', 'alerte'
    
    # Construire la requête de base
    detections = DetectionFaciale.objects.select_related(
        'camera', 'detenu'
    ).order_by('-timestamp')
    
    # Appliquer les filtres
    if search_query:
        detections = detections.filter(
            Q(detenu__nom__icontains=search_query) |
            Q(detenu__prenom__icontains=search_query) |
            Q(camera__nom__icontains=search_query)
        )
    
    if camera_id:
        detections = detections.filter(camera_id=camera_id)
    
    if detenu_id:
        detections = detections.filter(detenu_id=detenu_id)
    
    if date_debut:
        detections = detections.filter(timestamp__date__gte=date_debut)
    
    if date_fin:
        detections = detections.filter(timestamp__date__lte=date_fin)
    
    if statut == 'identifie':
        detections = detections.filter(detenu__isnull=False)
    elif statut == 'inconnu':
        detections = detections.filter(detenu__isnull=True)
    elif statut == 'alerte':
        detections = detections.filter(est_alerte=True)
    
    # Pagination
    paginator = Paginator(detections, 50)  # 50 détections par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    cameras = Camera.objects.all()
    detenus = Detenu.objects.all()
    
    context = {
        'page_obj': page_obj,
        'cameras': cameras,
        'detenus': detenus,
        'filters': {
            'search': search_query,
            'camera': camera_id,
            'detenu': detenu_id,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'statut': statut,
        },
        'total_count': detections.count(),
    }
    
    return render(request, 'surveillance/detections_list.html', context)


@login_required
def detection_image_view(request, detection_id):
    """Sert l'image d'une détection, ou un placeholder si le fichier manque."""
    detection = get_object_or_404(DetectionFaciale, id=detection_id)

    if detection.image_existe():
        return FileResponse(
            detection.image_detection.open('rb'),
            content_type='image/jpeg',
        )

    from io import BytesIO
    from PIL import Image, ImageDraw

    image = Image.new('RGB', (320, 240), color=(52, 58, 64))
    draw = ImageDraw.Draw(image)
    draw.text((70, 110), "Image indisponible", fill=(255, 255, 255))
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=80)
    buffer.seek(0)
    return FileResponse(buffer, content_type='image/jpeg')


@login_required
def detection_detail_view(request, detection_id):
    """Vue pour voir les détails d'une détection"""
    detection = get_object_or_404(
        DetectionFaciale.objects.select_related('camera', 'detenu'),
        id=detection_id
    )
    
    # Calculer les dimensions du visage
    coords = detection.coordonnees_visage or {}
    width = coords.get('right', 0) - coords.get('left', 0)
    height = coords.get('bottom', 0) - coords.get('top', 0)
    
    return render(request, 'surveillance/detection_detail.html', {
        'detection': detection,
        'face_width': width,
        'face_height': height
    })
