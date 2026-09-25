from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from io import BytesIO
import base64
import mimetypes
import os
import tempfile


try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except Exception:
    HTML = CSS = None
    WEASYPRINT_AVAILABLE = False


def media_to_data_uri(file_field):
    """Convertit un fichier média (photo) en data URI pour xhtml2pdf."""
    if not file_field:
        return None
    try:
        path = file_field.path
    except (ValueError, NotImplementedError):
        return None
    if not os.path.isfile(path):
        return None
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = 'image/jpeg'
    with open(path, 'rb') as handle:
        encoded = base64.b64encode(handle.read()).decode('ascii')
    return f'data:{mime};base64,{encoded}'


def _pdf_link_callback(uri, rel):
    if not uri or uri.startswith('data:'):
        return uri
    media_url = str(settings.MEDIA_URL)
    if uri.startswith(media_url):
        return os.path.join(str(settings.MEDIA_ROOT), uri[len(media_url):].lstrip('/').replace('/', os.sep))
    if uri.startswith('/media/'):
        return os.path.join(str(settings.MEDIA_ROOT), uri[len('/media/'):].replace('/', os.sep))
    return uri


def render_html_to_pdf(html_string, extra_css=None):
    """Génère un PDF depuis du HTML (WeasyPrint si GTK est dispo, sinon xhtml2pdf)."""
    if extra_css:
        html_string = f'<style type="text/css">{extra_css}</style>{html_string}'

    if WEASYPRINT_AVAILABLE:
        try:
            return HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()
        except Exception:
            pass

    from xhtml2pdf import pisa

    result = BytesIO()
    pdf = pisa.CreatePDF(
        src=html_string,
        dest=result,
        encoding='utf-8',
        link_callback=_pdf_link_callback,
    )
    if pdf.err:
        raise RuntimeError('La génération du PDF a échoué.')
    return result.getvalue()
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Detenu, StatutDetenu, TypePeine, CentrePenitencier, AdminPrison, TypeCentre, FicheDetenu, filtrer_enfants
from .forms import DetenuForm, LiberationForm, TransfertForm, RechercheDetenuForm, CentreForm, AdminPrisonForm


@login_required
def detenus_list_view(request, centre_id=None):
    """Liste des détenus avec recherche et filtrage"""
    # Récupérer les paramètres de recherche
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    regime = request.GET.get('regime', '')
    sexe = request.GET.get('sexe', '')
    mineur = request.GET.get('mineur', '')
    
    # Construire la requête de base selon le rôle de l'utilisateur
    user = request.user
    if centre_id:
        # Si un centre_id est fourni, filtrer par ce centre
        from django.shortcuts import get_object_or_404
        centre = get_object_or_404(CentrePenitencier, id=centre_id)
        
        # Vérifier les permissions
        if not user.is_admin_central():
            if hasattr(user, 'adminprison'):
                if user.adminprison.centre != centre:
                    messages.error(request, "Vous n'avez pas la permission de voir ce centre.")
                    return redirect('detenus_list')
            else:
                messages.error(request, "Vous n'avez pas la permission de voir les détenus.")
                return redirect('detenus_list')
        
        detenus = Detenu.objects.filter(centre=centre)
    elif user.is_admin_central():
        # L'admin central voit tous les détenus
        detenus = Detenu.objects.all()
    elif hasattr(user, 'adminprison'):
        # L'admin de centre ne voit que les détenus de son centre
        detenus = Detenu.objects.filter(centre=user.adminprison.centre)
    else:
        # Autres rôles ne voient rien (ou selon permissions)
        detenus = Detenu.objects.none()
    
    # Trier par date d'incarcération
    detenus = detenus.order_by('-date_incarceration')
    
    # Appliquer les filtres
    if search:
        detenus = detenus.filter(
            Q(nom__icontains=search) | 
            Q(prenom__icontains=search) | 
            Q(matricule__icontains=search)
        )
    
    if statut:
        detenus = detenus.filter(statut=statut)
    
    if regime:
        detenus = detenus.filter(regime=regime)
    
    if sexe:
        detenus = detenus.filter(sexe=sexe)

    if mineur == '1':
        detenus = filtrer_enfants(detenus)
    
    # Pagination
    paginator = Paginator(detenus, 20)  # 20 détenus par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Formulaire de recherche
    search_form = RechercheDetenuForm(request.GET)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_detenus': detenus.count(),
        'statuts': StatutDetenu.choices,
        'regimes': TypePeine.choices,
        'user_centre': user.adminprison.centre if hasattr(user, 'adminprison') else None,
        'can_edit': user.can_edit_detenus(),
        'centre': CentrePenitencier.objects.get(id=centre_id) if centre_id else None,
    }
    
    return render(request, 'detenus/list.html', context)


@login_required
def detenu_detail_view(request, detenu_id):
    """Détail d'un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    
    # Vérifier les permissions selon le rôle de l'utilisateur
    user = request.user
    if not user.is_admin_central():
        if hasattr(user, 'adminprison'):
            # L'admin de centre ne peut voir que les détenus de son centre
            if detenu.centre != user.adminprison.centre:
                messages.error(request, "Vous n'avez pas la permission de voir ce détenu.")
                return redirect('detenus_list')
        else:
            # Autres rôles ne peuvent pas voir les détenus
            messages.error(request, "Vous n'avez pas la permission de voir ce détenu.")
            return redirect('detenus_list')
    
    # Debug: vérifier les photos
    print(f"Détenu: {detenu.nom_complet}")
    print(f"Photo de face: {detenu.photo_face}")
    print(f"Photo de profil: {detenu.photo_profil}")
    if detenu.photo_face:
        print(f"URL photo face: {detenu.photo_face.url}")
    if detenu.photo_profil:
        print(f"URL photo profil: {detenu.photo_profil.url}")
    
    # Historique des modifications
    historique = detenu.historique.all().order_by('-created_at')[:10]
    visites = (
        detenu.visites.select_related('visiteur', 'agent_controle')
        .order_by('-date_visite')
    )

    context = {
        'detenu': detenu,
        'historique': historique,
        'visites': visites,
        'nb_visites': visites.count(),
        'nb_visites_terminees': visites.filter(statut='TERMINEE').count(),
        'nb_visites_programmees': visites.filter(statut='PROGRAMMEE').count(),
    }
    
    return render(request, 'detenus/detail_compact.html', context)


@login_required
def detenu_create_view(request):
    """Création d'un nouveau détenu"""
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_detenus():
        messages.error(request, "Vous n'avez pas la permission de créer des détenus.")
        return redirect('detenus_list')
    
    if request.method == 'POST':
        form = DetenuForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            detenu = form.save(commit=False)
            detenu.created_by = request.user
            
            # Assigner le centre selon le rôle de l'utilisateur
            if hasattr(user, 'adminprison'):
                # Admin de centre: assigner son centre
                detenu.centre = user.adminprison.centre
            elif user.is_admin_central():
                # Admin central: utiliser le centre du formulaire
                pass  # Le centre est déjà dans le formulaire
            else:
                messages.error(request, "Vous ne pouvez pas créer de détenu.")
                return redirect('detenus_list')
            
            detenu.save()
            
            messages.success(request, f'Détenu {detenu.nom_complet} créé avec succès.')
            return redirect('detenu_detail', detenu_id=detenu.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = DetenuForm(user=request.user)
        
        # Pré-remplir le centre pour les admins de centre
        if hasattr(user, 'adminprison'):
            form.initial['centre'] = user.adminprison.centre
            # Rendre le champ en lecture seule pour les admins de centre
            form.fields['centre'].widget.attrs['readonly'] = True
    
    context = {
        'form': form,
        'title': 'Nouveau détenu',
        'action': 'Créer',
        'user_centre': user.adminprison.centre if hasattr(user, 'adminprison') else None,
        'can_edit': user.can_edit_detenus(),
    }
    
    return render(request, 'detenus/form_compact.html', context)


@login_required
def detenu_edit_view(request, detenu_id):
    """Modification d'un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_detenus():
        messages.error(request, "Vous n'avez pas la permission de modifier les détenus.")
        return redirect('detenu_detail', detenu_id=detenu.id)
    
    # Vérifier que l'admin de centre ne modifie que les détenus de son centre
    if hasattr(user, 'adminprison'):
        if detenu.centre != user.adminprison.centre:
            messages.error(request, "Vous n'avez pas la permission de modifier ce détenu.")
            return redirect('detenu_detail', detenu_id=detenu.id)
    
    if request.method == 'POST':
        form = DetenuForm(request.POST, request.FILES, instance=detenu, user=request.user)
        if form.is_valid():
            detenu = form.save()
            
            # Debug: vérifier si les photos sont sauvegardées
            if detenu.photo_face:
                print(f"Photo de face mise à jour: {detenu.photo_face.path}")
            if detenu.photo_profil:
                print(f"Photo de profil mise à jour: {detenu.photo_profil.path}")
            
            messages.success(request, f'Détenu {detenu.nom_complet} modifié avec succès.')
            return redirect('detenu_detail', detenu_id=detenu.id)
        else:
            print("Erreurs formulaire:", form.errors)
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = DetenuForm(instance=detenu, user=request.user)
    
    context = {
        'form': form,
        'detenu': detenu,
        'title': f'Modifier {detenu.nom_complet}',
        'action': 'Modifier',
        'can_edit': user.can_edit_detenus(),
    }
    
    return render(request, 'detenus/form_compact.html', context)


@login_required
def detenu_delete_view(request, detenu_id):
    """Suppression d'un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_detenus():
        messages.error(request, "Vous n'avez pas la permission de supprimer les détenus.")
        return redirect('detenu_detail', detenu_id=detenu.id)
    
    # Vérifier que l'admin de centre ne supprime que les détenus de son centre
    if hasattr(user, 'adminprison'):
        if detenu.centre != user.adminprison.centre:
            messages.error(request, "Vous n'avez pas la permission de supprimer ce détenu.")
            return redirect('detenu_detail', detenu_id=detenu.id)
    
    if request.method == 'POST':
        nom_complet = detenu.nom_complet
        detenu.delete()
        messages.success(request, f'Détenu {nom_complet} supprimé avec succès.')
        return redirect('detenus_list')
    
    context = {
        'detenu': detenu,
        'can_edit': user.can_edit_detenus(),
    }
    
    return render(request, 'detenus/delete.html', context)


@login_required
def detenu_liberation_view(request, detenu_id):
    """Libération d'un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    
    if request.method == 'POST':
        form = LiberationForm(detenu, request.POST)
        if form.is_valid():
            detenu.date_liberation_effective = form.cleaned_data['date_liberation']
            detenu.motif_liberation = form.cleaned_data['motif_liberation']
            detenu.statut = StatutDetenu.LIBERE
            detenu.save()
            
            messages.success(request, f'Détenu {detenu.nom_complet} libéré avec succès.')
            return redirect('detenu_detail', detenu_id=detenu.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = LiberationForm(detenu)
    
    context = {
        'form': form,
        'detenu': detenu,
        'title': f'Libérer {detenu.nom_complet}',
    }
    
    return render(request, 'detenus/liberation.html', context)


@login_required
def detenu_transfert_view(request, detenu_id):
    """Transfert d'un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    
    if request.method == 'POST':
        form = TransfertForm(detenu, request.POST)
        if form.is_valid():
            # Créer un historique de transfert
            detenu.historique.create(
                action='TRANSFERT',
                description=f"Transfert vers {form.cleaned_data['destination']}",
                motif=form.cleaned_data['motif_transfert'],
                date_action=form.cleaned_data['date_transfert']
            )
            
            detenu.statut = StatutDetenu.TRANSFERE
            detenu.save()
            
            messages.success(request, f'Détenu {detenu.nom_complet} transféré avec succès.')
            return redirect('detenu_detail', detenu_id=detenu.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = TransfertForm(detenu)
    
    context = {
        'form': form,
        'detenu': detenu,
        'title': f'Transférer {detenu.nom_complet}',
    }
    
    return render(request, 'detenus/transfert.html', context)


@login_required
def detenu_stats_view(request):
    """Statistiques des détenus"""
    stats = {
        'total': Detenu.objects.count(),
        'incarceres': Detenu.objects.filter(statut=StatutDetenu.INCARCERE).count(),
        'liberes': Detenu.objects.filter(statut=StatutDetenu.LIBERE).count(),
        'transferes': Detenu.objects.filter(statut=StatutDetenu.TRANSFERE).count(),
        'evades': Detenu.objects.filter(statut=StatutDetenu.EVADE).count(),
        'decedes': Detenu.objects.filter(statut=StatutDetenu.DECEDE).count(),
        'enfants': filtrer_enfants(Detenu.objects.all()).count(),
        'enfants_incarceres': filtrer_enfants(Detenu.objects.all(), incarceres=True).count(),
    }
    
    # Statistiques par régime
    regimes_stats = {}
    for regime_code, regime_name in TypePeine.choices:
        regimes_stats[regime_name] = Detenu.objects.filter(regime=regime_code).count()
    
    # Statistiques par sexe
    sexe_stats = {
        'Masculin': Detenu.objects.filter(sexe='M').count(),
        'Féminin': Detenu.objects.filter(sexe='F').count(),
    }
    
    context = {
        'stats': stats,
        'regimes_stats': regimes_stats,
        'sexe_stats': sexe_stats,
    }
    
    return render(request, 'detenus/stats.html', context)


# API Views pour AJAX
@login_required
@require_http_methods(["GET"])
def api_cellules_centre(request):
    """Cellules d'un centre, filtrées par sexe si fourni."""
    from .cellules import cellules_json

    centre_id = request.GET.get('centre')
    sexe = request.GET.get('sexe') or ''
    user = request.user
    if not centre_id:
        return JsonResponse({'groups': []})

    centre = get_object_or_404(CentrePenitencier, pk=centre_id)
    if hasattr(user, 'adminprison') and user.adminprison.centre_id != centre.id:
        return JsonResponse({'groups': []}, status=403)
    if not (user.is_admin_central() or hasattr(user, 'adminprison')):
        return JsonResponse({'groups': []}, status=403)

    return JsonResponse({'groups': cellules_json(centre, sexe)})


@csrf_exempt
@require_http_methods(["GET"])
def api_detenu_search(request):
    """API de recherche de détenus pour AJAX"""
    search = request.GET.get('q', '')
    
    if len(search) < 2:
        return JsonResponse({'results': []})
    
    detenus = Detenu.objects.filter(
        Q(nom__icontains=search) | 
        Q(prenom__icontains=search) | 
        Q(matricule__icontains=search)
    )[:10]
    
    results = []
    for detenu in detenus:
        results.append({
            'id': detenu.id,
            'matricule': detenu.matricule,
            'nom_complet': detenu.nom_complet,
            'statut': detenu.get_statut_display(),
            'cellule': detenu.cellule,
        })
    
    return JsonResponse({'results': results})


@csrf_exempt
@require_http_methods(["POST"])
def api_detenu_quick_action(request, detenu_id):
    """API pour actions rapides sur un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    action = request.POST.get('action')
    
    if action == 'toggle_status':
        if detenu.statut == StatutDetenu.INCARCERE:
            detenu.statut = StatutDetenu.LIBERE
            detenu.save()
            return JsonResponse({
                'success': True,
                'message': f'{detenu.nom_complet} libéré',
                'new_status': detenu.get_statut_display()
            })
        else:
            detenu.statut = StatutDetenu.INCARCERE
            detenu.save()
            return JsonResponse({
                'success': True,
                'message': f'{detenu.nom_complet} incarcéré',
                'new_status': detenu.get_statut_display()
            })
    
    return JsonResponse({'success': False, 'message': 'Action non reconnue'})


@login_required
def download_photo_view(request, detenu_id, photo_type):
    """Vue pour télécharger les photos d'un détenu"""
    detenu = get_object_or_404(Detenu, id=detenu_id)
    
    if photo_type == 'face' and detenu.photo_face:
        photo_path = detenu.photo_face.path
        photo_name = f"photo_face_{detenu.matricule}.jpg"
    elif photo_type == 'profil' and detenu.photo_profil:
        photo_path = detenu.photo_profil.path
        photo_name = f"photo_profil_{detenu.matricule}.jpg"
    else:
        raise Http404("Photo non trouvée")
    
    try:
        with open(photo_path, 'rb') as photo_file:
            response = HttpResponse(photo_file.read(), content_type='image/jpeg')
            response['Content-Disposition'] = f'attachment; filename="{photo_name}"'
            return response
    except FileNotFoundError:
        raise Http404("Fichier non trouvé")


@login_required
def download_dossier_view(request, detenu_id):
    """Télécharge le dossier judiciaire joint à la fiche du détenu."""
    import mimetypes

    detenu = get_object_or_404(Detenu, id=detenu_id)
    user = request.user
    if hasattr(user, 'adminprison') and detenu.centre and detenu.centre != user.adminprison.centre:
        if not user.is_admin_central():
            raise Http404("Dossier non trouvé")

    if not detenu.dossier:
        raise Http404("Aucun dossier joint")

    try:
        file_path = detenu.dossier.path
    except ValueError:
        raise Http404("Fichier non trouvé")

    filename = os.path.basename(detenu.dossier.name)
    content_type, _ = mimetypes.guess_type(filename)
    try:
        with open(file_path, 'rb') as dossier_file:
            response = HttpResponse(
                dossier_file.read(),
                content_type=content_type or 'application/octet-stream',
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except FileNotFoundError:
        raise Http404("Fichier non trouvé")


@login_required
def biometric_capture_view(request):
    """Vue pour la capture biométrique avancée"""
    detenu = None
    
    # Récupérer le détenu si l'ID est fourni
    detenu_id = request.GET.get('detenu_id')
    if detenu_id:
        try:
            detenu = Detenu.objects.get(id=detenu_id)
        except Detenu.DoesNotExist:
            pass
    
    return render(request, 'detenus/biometric_capture.html', {
        'title': 'Capture Biométrique',
        'detenu': detenu
    })


@login_required
def dashboard_central_view(request):
    """Dashboard central pour l'administrateur central"""
    # Vérifier si l'utilisateur est admin central
    if not request.user.is_admin_central():
        messages.error(request, "Vous n'avez pas les permissions pour accéder à ce dashboard.")
        return redirect('detenus_list')
    
    # Statistiques globales
    stats = {
        'total_centres': CentrePenitencier.objects.count(),
        'centres_actifs': CentrePenitencier.objects.filter(statut=True).count(),
        'total_admins': AdminPrison.objects.count(),
        'admins_actifs': AdminPrison.objects.filter(statut=True).count(),
        'total_detenus': Detenu.objects.count(),
        'detenus_incarceres': Detenu.objects.filter(statut=StatutDetenu.INCARCERE).count(),
        'detenus_liberees': Detenu.objects.filter(statut=StatutDetenu.LIBERE).count(),
        'detenus_transferes': Detenu.objects.filter(statut=StatutDetenu.TRANSFERE).count(),
        # Statistiques par genre
        'total_hommes': Detenu.objects.filter(sexe='M').count(),
        'total_femmes': Detenu.objects.filter(sexe='F').count(),
        'hommes_incarceres': Detenu.objects.filter(sexe='M', statut=StatutDetenu.INCARCERE).count(),
        'femmes_incarceres': Detenu.objects.filter(sexe='F', statut=StatutDetenu.INCARCERE).count(),
        'enfants': filtrer_enfants(Detenu.objects.all()).count(),
        'enfants_incarceres': filtrer_enfants(Detenu.objects.all(), incarceres=True).count(),
    }
    
    # Capacité totale
    capacite_stats = CentrePenitencier.objects.aggregate(
        capacite_max=Sum('capacite_max'),
        capacite_actuelle=Sum('capacite_actuelle')
    )
    stats['capacite_totale'] = capacite_stats['capacite_max'] or 0
    stats['capacite_utilisee'] = capacite_stats['capacite_actuelle'] or 0
    stats['places_disponibles'] = stats['capacite_totale'] - stats['capacite_utilisee']
    
    if stats['capacite_totale'] > 0:
        stats['taux_occupation_global'] = (stats['capacite_utilisee'] / stats['capacite_totale']) * 100
    else:
        stats['taux_occupation_global'] = 0
    
    # Centres par type
    stats['centres_par_type'] = [
        (label, CentrePenitencier.objects.filter(type_centre=value).count())
        for value, label in TypeCentre.choices
    ]
    
    # Centres les plus chargés
    centres_plus_charges = CentrePenitencier.objects.filter(
        capacite_max__gt=0
    ).order_by('-capacite_actuelle')[:5]

    centres_occ = sorted(
        CentrePenitencier.objects.filter(capacite_max__gt=0),
        key=lambda c: c.taux_occupation,
        reverse=True,
    )[:8]
    graphiques = {
        'sexe': {
            'labels': ['Hommes incarcérés', 'Femmes incarcérées'],
            'values': [stats['hommes_incarceres'], stats['femmes_incarceres']],
        },
        'occupation': {
            'labels': [
                (c.nom if len(c.nom) <= 28 else c.nom[:26] + '…')
                for c in centres_occ
            ],
            'values': [round(c.taux_occupation, 1) for c in centres_occ],
        },
    }
    
    # Derniers admins créés
    derniers_admins = AdminPrison.objects.select_related('utilisateur', 'centre').order_by('-created_at')[:5]
    
    # Activité récente (détenus créés/modifiés)
    activite_recente = Detenu.objects.order_by('-updated_at')[:10]
    
    return render(request, 'detenus/dashboard_central.html', {
        'title': 'Dashboard Central - Gestion des Prisons',
        'stats': stats,
        'centres_plus_charges': centres_plus_charges,
        'derniers_admins': derniers_admins,
        'activite_recente': activite_recente,
        'graphiques': graphiques,
    })


@login_required
def centres_list_view(request):
    """Liste des centres pénitenciers"""
    # Seul l'admin central peut voir tous les centres
    # Les admins de centre ne voient que leur centre
    user = request.user
    if not user.can_view_all_centres():
        messages.error(request, "Vous n'avez pas la permission de voir les centres.")
        return redirect('dashboard_central' if user.is_admin_central() else 'detenus_list')
    
    centres = CentrePenitencier.objects.all().prefetch_related('photos').order_by('nom')
    
    # Filtrer par type si spécifié
    type_centre = request.GET.get('type_centre')
    if type_centre:
        centres = centres.filter(type_centre=type_centre)
    
    # Filtrer par statut si spécifié
    statut = request.GET.get('statut')
    if statut:
        centres = centres.filter(statut=statut == 'actif')

    province = request.GET.get('province')
    if province:
        centres = centres.filter(province=province)

    provinces = (
        CentrePenitencier.objects.exclude(province='')
        .order_by('province')
        .values_list('province', flat=True)
        .distinct()
    )
    
    return render(request, 'detenus/centres_list.html', {
        'title': 'Centres Pénitenciers',
        'centres': centres,
        'type_centre': type_centre,
        'statut': statut,
        'province': province,
        'provinces': provinces,
        'centres_types': TypeCentre.choices,
        'nb_centres': centres.count(),
        'nb_actifs': centres.filter(statut=True).count(),
        'nb_inactifs': centres.filter(statut=False).count(),
    })


@login_required
def admins_prison_list_view(request):
    """Liste des administrateurs de prison"""
    try:
        # Seul l'admin central peut voir tous les admins
        # Les admins de centre ne voient que les admins de leur centre
        user = request.user
        if not user.can_view_all_data() and not hasattr(user, 'adminprison'):
            messages.error(request, "Vous n'avez pas la permission de voir les administrateurs.")
            return redirect('dashboard_central' if user.is_admin_central() else 'detenus_list')
        
        admins = AdminPrison.objects.select_related('utilisateur', 'centre').order_by('centre__nom', 'utilisateur__last_name', 'utilisateur__first_name')
        
        # Si l'utilisateur est un admin de centre, il ne voit que les admins de son centre
        if hasattr(user, 'adminprison'):
            admins = admins.filter(centre=user.adminprison.centre)
        
        # Filtrer par centre si spécifié
        centre_id = request.GET.get('centre')
        if centre_id:
            admins = admins.filter(centre_id=centre_id)
        
        # Filtrer par statut si spécifié
        statut = request.GET.get('statut')
        if statut:
            admins = admins.filter(statut=statut == 'actif')
        
        centres = CentrePenitencier.objects.filter(statut=True).order_by('nom')
        
        # Message si aucune donnée (uniquement si aucun filtre n'est appliqué)
        has_filters = centre_id or statut
        if not admins.exists() and not has_filters:
            messages.info(request, "Aucun administrateur de prison trouvé. Veuillez d'abord créer des centres et des administrateurs.")
        elif not admins.exists() and has_filters:
            messages.info(request, "Aucun administrateur ne correspond aux critères de recherche.")
        
        return render(request, 'detenus/admins_prison_list.html', {
            'title': 'Administrateurs de Prison',
            'admins': admins,
            'centres': centres,
            'centre_id': centre_id,
            'statut': statut,
        })
    except Exception as e:
        print(f"ERROR in admins_prison_list_view: {e}")
        messages.error(request, f"Erreur: {str(e)}")
        return render(request, 'detenus/admins_prison_list.html', {
            'title': 'Administrateurs de Prison',
            'admins': AdminPrison.objects.none(),
            'centres': CentrePenitencier.objects.filter(statut=True).order_by('nom'),
            'centre_id': None,
            'statut': None,
        })


@login_required
def admin_prison_detail_view(request, admin_id):
    """Détails d'un administrateur de prison"""
    try:
        admin = get_object_or_404(AdminPrison, id=admin_id)
        
        # Vérifier les permissions
        user = request.user
        if hasattr(user, 'adminprison') and admin.centre != user.adminprison.centre:
            messages.error(request, "Vous n'avez pas la permission de voir cet administrateur.")
            return redirect('admins_prison_list')
        
        return render(request, 'detenus/admin_prison_detail.html', {
            'title': f'Détails - {admin.utilisateur.get_full_name()}',
            'admin': admin,
        })
    except Exception as e:
        print(f"ERROR in admin_prison_detail_view: {e}")
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('admins_prison_list')


@login_required
def admin_prison_edit_view(request, admin_id):
    """Modifier un administrateur de prison"""
    try:
        admin = get_object_or_404(AdminPrison, id=admin_id)
        
        # Vérifier les permissions
        user = request.user
        if user.can_create_admins():
            pass
        elif hasattr(user, 'adminprison') and admin.centre == user.adminprison.centre:
            pass
        else:
            messages.error(request, "Vous n'avez pas la permission de modifier cet administrateur.")
            return redirect('admins_prison_list')
        
        if request.method == 'POST':
            # Mettre à jour les champs
            admin.poste = request.POST.get('poste', admin.poste)
            admin.date_affectation = request.POST.get('date_affectation', admin.date_affectation)
            admin.statut = 'statut' in request.POST
            
            # Mettre à jour l'utilisateur si nécessaire
            utilisateur = admin.utilisateur
            utilisateur.first_name = request.POST.get('first_name', utilisateur.first_name)
            utilisateur.last_name = request.POST.get('last_name', utilisateur.last_name)
            utilisateur.email = request.POST.get('email', utilisateur.email)
            utilisateur.telephone = request.POST.get('telephone', utilisateur.telephone)
            utilisateur.save()
            
            admin.save()
            
            messages.success(request, "Administrateur modifié avec succès.")
            return redirect('admin_prison_detail', admin_id=admin_id)
        
        centres = CentrePenitencier.objects.filter(statut=True).order_by('nom')
        
        return render(request, 'detenus/admin_prison_edit.html', {
            'title': f'Modifier - {admin.utilisateur.get_full_name()}',
            'admin': admin,
            'centres': centres,
        })
    except Exception as e:
        print(f"ERROR in admin_prison_edit_view: {e}")
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('admins_prison_list')


@login_required
@require_http_methods(["POST"])
def admin_prison_toggle_status_view(request, admin_id):
    """Basculer le statut d'un administrateur de prison"""
    try:
        admin = get_object_or_404(AdminPrison, id=admin_id)
        
        # Vérifier les permissions
        user = request.user
        if user.can_create_admins():
            pass
        elif hasattr(user, 'adminprison') and admin.centre == user.adminprison.centre:
            pass
        else:
            return JsonResponse({
                'success': False,
                'error': 'Vous n\'avez pas la permission de modifier cet administrateur.'
            }, status=403)
        
        # Basculer le statut
        admin.statut = not admin.statut
        admin.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Administrateur {"activé" if admin.statut else "désactivé"} avec succès.',
            'new_status': admin.statut
        })
        
    except Exception as e:
        print(f"ERROR in admin_prison_toggle_status_view: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def centre_dashboard_view(request, centre_id):
    """Dashboard pour l'admin d'un centre spécifique"""
    try:
        # Vérifier les permissions
        user = request.user
        centre = get_object_or_404(
            CentrePenitencier.objects.prefetch_related('photos'),
            id=centre_id,
        )
        
        # L'admin central peut voir tous les centres
        # L'admin de centre ne peut voir que son centre
        if not user.is_admin_central():
            if not hasattr(user, 'adminprison') or user.adminprison.centre != centre:
                messages.error(request, "Vous n'avez pas la permission de voir ce centre.")
                return redirect('detenus_list')
        
        # Statistiques du centre
        stats = {
            'total_detenus': Detenu.objects.filter(centre=centre).count(),
            'detenus_incarceres': Detenu.objects.filter(centre=centre, statut=StatutDetenu.INCARCERE).count(),
            'detenus_liberees': Detenu.objects.filter(centre=centre, statut=StatutDetenu.LIBERE).count(),
            'detenus_transferes': Detenu.objects.filter(centre=centre, statut=StatutDetenu.TRANSFERE).count(),
            'capacite_max': centre.capacite_max,
            'capacite_actuelle': centre.capacite_actuelle,
            'places_disponibles': centre.places_disponibles,
            'taux_occupation': centre.taux_occupation,
            # Statistiques par genre pour ce centre
            'total_hommes': Detenu.objects.filter(centre=centre, sexe='M').count(),
            'total_femmes': Detenu.objects.filter(centre=centre, sexe='F').count(),
            'hommes_incarceres': Detenu.objects.filter(centre=centre, sexe='M', statut=StatutDetenu.INCARCERE).count(),
            'femmes_incarceres': Detenu.objects.filter(centre=centre, sexe='F', statut=StatutDetenu.INCARCERE).count(),
            'enfants': filtrer_enfants(Detenu.objects.filter(centre=centre)).count(),
            'enfants_incarceres': filtrer_enfants(
                Detenu.objects.filter(centre=centre), incarceres=True
            ).count(),
        }
        
        # Derniers détenus du centre
        derniers_detenus = Detenu.objects.filter(centre=centre).order_by('-created_at')[:10]
        
        # Admins du centre
        admins_centre = AdminPrison.objects.filter(centre=centre).select_related('utilisateur')
        
        # Activité récente du centre
        activite_recente = Detenu.objects.filter(centre=centre).order_by('-updated_at')[:10]
        
        return render(request, 'detenus/centre_dashboard.html', {
            'title': f'Dashboard - {centre.nom}',
            'centre': centre,
            'stats': stats,
            'derniers_detenus': derniers_detenus,
            'admins_centre': admins_centre,
            'activite_recente': activite_recente,
        })
    except Exception as e:
        print(f"ERROR in centre_dashboard_view: {e}")
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('detenus_list')


@login_required
def generer_liste_detenus_centre(request, centre_id):
    """Générer la liste des détenus d'un centre en PDF"""
    # Vérifier que l'utilisateur est un admin de centre
    if not hasattr(request.user, 'adminprison'):
        messages.error(request, "Seul un administrateur de centre peut générer cette liste.")
        return redirect('dashboard')
    
    # Vérifier que le centre appartient à l'admin
    admin_prison = request.user.adminprison
    if admin_prison.centre.id != centre_id:
        messages.error(request, "Vous n'avez pas accès à ce centre.")
        return redirect('dashboard')
    
    centre = get_object_or_404(CentrePenitencier, id=centre_id)
    
    # Récupérer les détenus du centre
    detenus = Detenu.objects.filter(centre=centre).order_by('nom', 'prenom')
    
    # Statistiques
    stats = {
        'total_detenus': detenus.count(),
        'incarceres': detenus.filter(statut=StatutDetenu.INCARCERE).count(),
        'liberes': detenus.filter(statut=StatutDetenu.LIBERE).count(),
        'transferes': detenus.filter(statut=StatutDetenu.TRANSFERE).count(),
        'evides': detenus.filter(statut=StatutDetenu.EVADE).count(),
        'decedes': detenus.filter(statut=StatutDetenu.DECEDE).count(),
    }
    
    # Préparer le contexte pour le template PDF
    context = {
        'centre': centre,
        'detenus': detenus,
        'stats': stats,
        'date_generation': timezone.now(),
        'admin': admin_prison,
    }
    
    try:
        # Générer le HTML
        html_string = render_to_string('detenus/pdf_liste_detenus.html', context)
        pdf = render_html_to_pdf(html_string)
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="liste_detenus_{centre.code}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('centre_dashboard', centre_id=centre_id)


@login_required
def centre_create_view(request):
    """Créer un nouveau centre pénitencier"""
    if not request.user.can_create_centres():
        messages.error(request, "Vous n'avez pas la permission de créer des centres.")
        return redirect('centres_list')
    
    if request.method == 'POST':
        form = CentreForm(request.POST, request.FILES)
        if form.is_valid():
            centre = form.save()
            nb_photos = centre.photos.count()
            if nb_photos:
                messages.success(
                    request,
                    f"Centre '{centre.nom}' créé avec succès ({nb_photos} photo{'s' if nb_photos > 1 else ''}).",
                )
            else:
                messages.success(request, f"Centre '{centre.nom}' créé avec succès.")
            return redirect('centres_list')
    else:
        form = CentreForm()
    
    return render(request, 'detenus/centre_form.html', {
        'title': 'Créer un Nouveau Centre',
        'form': form,
        'action': 'Créer',
        'centre': None,
    })


@login_required
def centre_edit_view(request, centre_id):
    """Modifier un centre pénitencier (admin central)."""
    if not request.user.can_edit_centre_info():
        messages.error(request, "Vous n'avez pas la permission de modifier ce centre.")
        return redirect('centre_dashboard', centre_id=centre_id)

    centre = get_object_or_404(
        CentrePenitencier.objects.prefetch_related('photos'),
        id=centre_id,
    )

    if request.method == 'POST':
        form = CentreForm(request.POST, request.FILES, instance=centre)
        if form.is_valid():
            centre = form.save()
            messages.success(request, f"Centre '{centre.nom}' mis à jour.")
            return redirect('centre_dashboard', centre_id=centre.id)
    else:
        form = CentreForm(instance=centre)

    return render(request, 'detenus/centre_form.html', {
        'title': f'Modifier — {centre.nom}',
        'form': form,
        'action': 'Enregistrer',
        'centre': centre,
    })


@login_required
def admin_prison_create_view(request):
    """Créer un nouvel administrateur de prison"""
    if not request.user.can_create_admins():
        messages.error(request, "Vous n'avez pas la permission de créer des administrateurs.")
        return redirect('admins_prison_list')
    
    if request.method == 'POST':
        form = AdminPrisonForm(request.POST)
        if form.is_valid():
            admin = form.save()
            messages.success(request, f"Administrateur '{admin.utilisateur.get_full_name()}' créé avec succès.")
            return redirect('admins_prison_list')
    else:
        form = AdminPrisonForm()
    
    return render(request, 'detenus/admin_prison_form.html', {
        'title': 'Créer un Nouvel Administrateur',
        'form': form,
        'action': 'Créer'
    })


@login_required
def generer_fiche_detenu(request, detenu_id):
    """Générer la fiche d'identification d'un détenu en PDF"""
    try:
        # Récupérer le détenu
        detenu = get_object_or_404(Detenu, id=detenu_id)
        
        # Vérifier les permissions
        user = request.user
        if not user.can_manage_centre_detenus():
            messages.error(request, "Vous n'avez pas la permission de générer des fiches.")
            return redirect('detenus_list')
        
        # Créer la fiche si elle n'existe pas
        fiche, created = FicheDetenu.objects.get_or_create(
            detenu=detenu,
            defaults={
                'valide_par': user,
                'statut_validation': 'VALIDE'
            }
        )
        
        # Calculer les informations supplémentaires
        aujourd_hui = timezone.now().date()
        date_incarceration = detenu.date_incarceration
        
        if date_incarceration:
            duree_detention = (aujourd_hui - date_incarceration).days
        else:
            duree_detention = 0
        
        # Calculer l'âge
        if detenu.date_naissance:
            age = aujourd_hui.year - detenu.date_naissance.year - (
                (aujourd_hui.month, aujourd_hui.day) < (detenu.date_naissance.month, detenu.date_naissance.day)
            )
        else:
            age = 0
        
        # Préparer le contexte pour le template PDF
        # Construire l'URL absolue de la photo si elle existe
        photo_url = media_to_data_uri(detenu.photo_face) or media_to_data_uri(detenu.photo_profil)
        
        context = {
            'fiche': fiche,
            'detenu': detenu,
            'age': age,
            'duree_detention': duree_detention,
            'date_generation': timezone.now(),
            'utilisateur': user,
            'photo_url': photo_url,
        }
        
        # Générer le HTML
        html_string = render_to_string('detenus/fiche_detenu.html', context)
        pdf = render_html_to_pdf(html_string)
        
        # Préparer la réponse HTTP
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"fiche_detenu_{detenu.matricule}_{detenu.nom}_{detenu.prenom}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération de la fiche: {str(e)}")
        return redirect('detenu_detail', detenu_id=detenu_id)
