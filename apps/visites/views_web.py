from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Visiteur, Visite, ObjetVisite, TypeVisiteur, StatutVisite
from .forms import VisiteurForm, VisiteForm, ObjetVisiteForm
from apps.comptes.models import Utilisateur
from apps.detenus.models import Detenu, CentrePenitencier


@login_required
def visiteurs_list_view(request):
    """Liste des visiteurs avec recherche et filtrage"""
    if not request.user.can_view_visites():
        messages.error(request, "Vous n'avez pas la permission de consulter les visiteurs.")
        return redirect('dashboard')

    # Récupérer les paramètres de recherche
    search = request.GET.get('search', '')
    type_visiteur = request.GET.get('type_visiteur', '')
    
    # Construire la requête
    visiteurs = Visiteur.objects.all().order_by('nom', 'prenom')
    
    # Appliquer les filtres
    if search:
        visiteurs = visiteurs.filter(
            Q(nom__icontains=search) | 
            Q(prenom__icontains=search) |
            Q(numero_piece__icontains=search)
        )
    
    if type_visiteur:
        visiteurs = visiteurs.filter(type_visiteur=type_visiteur)
    
    # Pagination
    paginator = Paginator(visiteurs, 20)  # 20 visiteurs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_visiteurs': visiteurs.count(),
        'nb_famille': visiteurs.filter(type_visiteur=TypeVisiteur.FAMILLE).count(),
        'nb_avocats': visiteurs.filter(type_visiteur=TypeVisiteur.AVOCAT).count(),
        'nb_amis': visiteurs.filter(type_visiteur=TypeVisiteur.AMI).count(),
        'nb_autres': visiteurs.exclude(
            type_visiteur__in=[TypeVisiteur.FAMILLE, TypeVisiteur.AVOCAT, TypeVisiteur.AMI]
        ).count(),
        'types_visiteur': TypeVisiteur.choices,
    }
    
    return render(request, 'visites/visiteurs_list.html', context)


@login_required
def visiteur_detail_view(request, visiteur_id):
    """Détail d'un visiteur"""
    if not request.user.can_view_visites():
        messages.error(request, "Vous n'avez pas la permission de consulter les visiteurs.")
        return redirect('dashboard')

    visiteur = get_object_or_404(Visiteur, id=visiteur_id)
    
    visites = visiteur.visites.select_related('detenu', 'detenu__centre').order_by('-date_visite')
    if request.user.is_admin_central():
        pass
    elif hasattr(request.user, 'adminprison'):
        visites = visites.filter(detenu__centre=request.user.adminprison.centre)
    visites = visites[:10]
    
    context = {
        'visiteur': visiteur,
        'visites': visites,
    }
    
    return render(request, 'visites/visiteur_detail.html', context)


@login_required
def visiteur_create_view(request):
    """Création d'un nouveau visiteur"""
    if not request.user.can_edit_visites():
        messages.error(request, "Vous n'avez pas la permission de créer un visiteur.")
        return redirect('visiteurs_list')
    if request.method == 'POST':
        form = VisiteurForm(request.POST, request.FILES)
        if form.is_valid():
            visiteur = form.save()
            messages.success(request, f'Visiteur {visiteur.nom_complet} créé avec succès.')
            return redirect('visiteur_detail', visiteur_id=visiteur.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = VisiteurForm()
    
    context = {
        'form': form,
        'title': 'Nouveau visiteur',
        'action': 'Créer'
    }
    
    return render(request, 'visites/visiteur_form_compact.html', context)


@login_required
def visiteur_edit_view(request, visiteur_id):
    """Modification d'un visiteur"""
    visiteur = get_object_or_404(Visiteur, id=visiteur_id)
    if not request.user.can_edit_visites():
        messages.error(request, "Vous n'avez pas la permission de modifier un visiteur.")
        return redirect('visiteur_detail', visiteur_id=visiteur.id)
    
    if request.method == 'POST':
        form = VisiteurForm(request.POST, request.FILES, instance=visiteur)
        if form.is_valid():
            visiteur = form.save()
            messages.success(request, f'Visiteur {visiteur.nom_complet} modifié avec succès.')
            return redirect('visiteur_detail', visiteur_id=visiteur.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = VisiteurForm(instance=visiteur)
    
    context = {
        'form': form,
        'visiteur': visiteur,
        'title': f'Modifier {visiteur.nom_complet}',
        'action': 'Modifier'
    }
    
    return render(request, 'visites/visiteur_form_compact.html', context)


@login_required
def visites_list_view(request):
    """Liste des visites avec recherche et filtrage"""
    from django.utils import timezone
    
    user = request.user
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    detenu_id = request.GET.get('detenu', '')
    centre_id = request.GET.get('centre', '')
    custom_date = request.GET.get('custom_date', '')
    date_filter = request.GET.get('date')
    if not date_filter:
        date_filter = 'all' if user.is_admin_central() else 'today'

    if not user.can_view_visites():
        visites = Visite.objects.none()
    elif user.is_admin_central():
        visites = Visite.objects.all()
    elif hasattr(user, 'adminprison'):
        visites = Visite.objects.filter(detenu__centre=user.adminprison.centre)
    else:
        visites = Visite.objects.none()

    visites = visites.select_related(
        'visiteur', 'detenu', 'detenu__centre', 'agent_controle'
    ).order_by('-date_visite')

    if centre_id and user.is_admin_central():
        visites = visites.filter(detenu__centre_id=centre_id)

    centre_filtre = None
    if centre_id:
        centre_filtre = CentrePenitencier.objects.filter(pk=centre_id).first()
    
    # Filtrer par date (la date personnalisée ne s'applique que si la période = custom)
    if date_filter == 'custom' and custom_date:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(custom_date, '%Y-%m-%d').date()
            visites = visites.filter(date_visite__date=date_obj)
        except ValueError:
            aujourd_hui = timezone.now().date()
            visites = visites.filter(date_visite__date=aujourd_hui)
    elif date_filter == 'today':
        aujourd_hui = timezone.now().date()
        visites = visites.filter(date_visite__date=aujourd_hui)
    elif date_filter == 'week':
        from datetime import timedelta
        debut_semaine = timezone.now().date() - timedelta(days=7)
        visites = visites.filter(date_visite__date__gte=debut_semaine)
    elif date_filter == 'month':
        debut_mois = timezone.now().date().replace(day=1)
        visites = visites.filter(date_visite__date__gte=debut_mois)
    elif date_filter == 'all':
        # Aucun filtre de date - afficher toutes les visites
        pass
    
    # Appliquer les filtres
    if search:
        visites = visites.filter(
            Q(visiteur__nom__icontains=search) |
            Q(visiteur__prenom__icontains=search) |
            Q(detenu__nom__icontains=search) |
            Q(detenu__prenom__icontains=search) |
            Q(detenu__matricule__icontains=search)
        )
    
    if statut:
        visites = visites.filter(statut=statut)
    
    if detenu_id:
        visites = visites.filter(detenu_id=detenu_id)

    if user.is_admin_central():
        detenus = Detenu.objects.all()
        if centre_id:
            detenus = detenus.filter(centre_id=centre_id)
        detenus = detenus.order_by('nom', 'prenom')
        centres = CentrePenitencier.objects.filter(statut=True).order_by('nom')
    elif hasattr(user, 'adminprison'):
        detenus = Detenu.objects.filter(centre=user.adminprison.centre).order_by('nom', 'prenom')
        centres = CentrePenitencier.objects.none()
    else:
        detenus = Detenu.objects.none()
        centres = CentrePenitencier.objects.none()
    
    # Pagination
    paginator = Paginator(visites, 20)  # 20 visites par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_visites': visites.count(),
        'nb_programmees': visites.filter(statut=StatutVisite.PROGRAMMEE).count(),
        'nb_en_cours': visites.filter(statut=StatutVisite.EN_COURS).count(),
        'nb_terminees': visites.filter(statut=StatutVisite.TERMINEE).count(),
        'nb_annulees': visites.filter(statut=StatutVisite.ANNULEE).count(),
        'statuts': StatutVisite.choices,
        'detenus': detenus,
        'centres': centres,
        'centre_id': centre_id,
        'centre_filtre': centre_filtre,
        'date_filter': date_filter,
        'custom_date': custom_date,
        'search': search,
        'statut': statut,
        'detenu_id': detenu_id,
        'today': timezone.now().date().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'visites/visites_list.html', context)


@login_required
def visite_detail_view(request, visite_id):
    """Détail d'une visite"""
    user = request.user
    if not user.can_view_visites():
        messages.error(request, "Vous n'avez pas la permission de consulter les visites.")
        return redirect('dashboard')

    visite = get_object_or_404(
        Visite.objects.select_related('visiteur', 'detenu', 'detenu__centre', 'agent_controle'),
        id=visite_id,
    )
    if hasattr(user, 'adminprison') and not user.is_admin_central():
        if visite.detenu.centre != user.adminprison.centre:
            messages.error(request, "Vous n'avez pas la permission de voir cette visite.")
            return redirect('visites_list')
    
    # Objets de la visite
    objets = visite.objets.all().order_by('nom_objet')
    
    context = {
        'visite': visite,
        'objets': objets,
    }
    
    return render(request, 'visites/visite_detail_compact.html', context)


@login_required
def visite_create_view(request):
    """Création d'une nouvelle visite"""
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_visites():
        messages.error(request, "Vous n'avez pas la permission de créer des visites.")
        return redirect('visites_list')
    
    if request.method == 'POST':
        form = VisiteForm(request.POST, user=request.user)
        if form.is_valid():
            visite = form.save(commit=False)
            visite.created_by = request.user
            visite.save()
            messages.success(request, f'Visite programmée avec succès.')
            return redirect('visite_detail', visite_id=visite.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = VisiteForm(user=request.user)
        detenu_id = request.GET.get('detenu')
        if detenu_id:
            form.initial['detenu'] = detenu_id
            if 'detenu' in form.fields:
                form.fields['detenu'].initial = detenu_id
    
    context = {
        'form': form,
        'title': 'Nouvelle visite',
        'action': 'Programmer',
        'can_edit': user.can_edit_visites(),
    }
    
    return render(request, 'visites/visite_form_compact.html', context)


@login_required
def visite_edit_view(request, visite_id):
    """Modification d'une visite"""
    visite = get_object_or_404(Visite, id=visite_id)
    
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_visites():
        messages.error(request, "Vous n'avez pas la permission de modifier les visites.")
        return redirect('visite_detail', visite_id=visite.id)
    
    # Vérifier que l'admin de centre ne modifie que les visites des détenus de son centre
    if hasattr(user, 'adminprison'):
        if visite.detenu.centre != user.adminprison.centre:
            messages.error(request, "Vous n'avez pas la permission de modifier cette visite.")
            return redirect('visite_detail', visite_id=visite.id)
    
    if request.method == 'POST':
        form = VisiteForm(request.POST, instance=visite, user=request.user)
        if form.is_valid():
            visite = form.save()
            messages.success(request, f'Visite modifiée avec succès.')
            return redirect('visite_detail', visite_id=visite.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = VisiteForm(instance=visite, user=request.user)
    
    context = {
        'form': form,
        'visite': visite,
        'title': 'Modifier la visite',
        'action': 'Modifier',
        'can_edit': user.can_edit_visites(),
    }
    
    return render(request, 'visites/visite_form_compact.html', context)


@login_required
def visite_delete_view(request, visite_id):
    """Suppression d'une visite"""
    visite = get_object_or_404(Visite, id=visite_id)
    
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_visites():
        messages.error(request, "Vous n'avez pas la permission de supprimer des visites.")
        return redirect('visite_detail', visite_id=visite.id)
    
    # Vérifier que l'admin de centre ne supprime que les visites des détenus de son centre
    if hasattr(user, 'adminprison'):
        if visite.detenu.centre != user.adminprison.centre:
            messages.error(request, "Vous n'avez pas la permission de supprimer cette visite.")
            return redirect('visite_detail', visite_id=visite.id)
    
    if request.method == 'POST':
        visite.delete()
        messages.success(request, 'Visite supprimée avec succès.')
        return redirect('visites_list')
    
    context = {
        'visite': visite,
        'can_edit': user.can_edit_visites(),
    }
    
    return render(request, 'visites/visite_confirm_delete.html', context)


# API Views pour AJAX
@csrf_exempt
@require_http_methods(["GET"])
def api_visiteur_search(request):
    """API de recherche de visiteurs pour AJAX"""
    search = request.GET.get('q', '')
    
    if len(search) < 2:
        return JsonResponse({'results': []})
    
    visiteurs = Visiteur.objects.filter(
        Q(nom__icontains=search) | 
        Q(prenom__icontains=search)
    )[:10]
    
    results = []
    for visiteur in visiteurs:
        results.append({
            'id': visiteur.id,
            'nom_complet': visiteur.nom_complet,
            'type_visiteur': visiteur.get_type_visiteur_display(),
            'numero_piece': visiteur.numero_piece,
        })
    
    return JsonResponse({'results': results})


@csrf_exempt
@require_http_methods(["POST"])
def api_visite_action(request, visite_id):
    """API pour actions sur une visite"""
    visite = get_object_or_404(Visite, id=visite_id)
    action = request.POST.get('action')
    
    if action == 'commencer':
        visite.statut = StatutVisite.EN_COURS
        visite.save()
        return JsonResponse({'success': True, 'message': 'Visite commencée'})
    
    elif action == 'terminer':
        visite.statut = StatutVisite.TERMINEE
        visite.save()
        return JsonResponse({'success': True, 'message': 'Visite terminée'})
    
    elif action == 'annuler':
        visite.statut = StatutVisite.ANNULEE
        visite.save()
        return JsonResponse({'success': True, 'message': 'Visite annulée'})
    
    return JsonResponse({'success': False, 'message': 'Action non reconnue'})


SEUIL_RELAIS_JOURS = 7
_STATUTS_PONT = (
    StatutVisite.PROGRAMMEE,
    StatutVisite.EN_COURS,
    StatutVisite.TERMINEE,
)


def _analyser_pont_communication(visites):
    """Repère un visiteur susceptible de relier des détenus de prisons différentes (probable pont)."""
    utiles = [
        v for v in visites
        if v.statut in _STATUTS_PONT and v.detenu_id and v.detenu.centre_id
    ]
    chrono = sorted(utiles, key=lambda v: v.date_visite)
    prisons = {v.detenu.centre_id for v in chrono}
    detenus = {v.detenu_id for v in chrono}
    est_pont = len(prisons) > 1 and len(detenus) > 1
    relais = []
    for i, premiere in enumerate(chrono):
        for suivante in chrono[i + 1:]:
            if premiere.detenu_id == suivante.detenu_id:
                continue
            if premiere.detenu.centre_id == suivante.detenu.centre_id:
                continue
            delta = suivante.date_visite - premiere.date_visite
            jours = abs(delta.total_seconds()) / 86400
            relais.append({
                'de': premiere,
                'vers': suivante,
                'jours': jours,
                'rapide': jours <= SEUIL_RELAIS_JOURS,
            })
    relais.sort(key=lambda r: (not r['rapide'], r['jours']))
    return {
        'est_pont': est_pont,
        'relais': relais,
        'nb_relais_rapides': sum(1 for r in relais if r['rapide']),
        'seuil_jours': SEUIL_RELAIS_JOURS,
    }


@login_required
def suivi_visiteur_view(request):
    """Parcours d'un visiteur dans plusieurs prisons et auprès de plusieurs détenus (admin central)."""
    if not request.user.is_admin_central():
        messages.error(request, "Le suivi national des visiteurs est réservé à l'administrateur central.")
        return redirect('dashboard')

    search = request.GET.get('search', '').strip()
    centre_id = request.GET.get('centre', '')
    detenu_id = request.GET.get('detenu', '')
    parcours = request.GET.get('parcours', '')
    visiteur_id = request.GET.get('visiteur', '')

    visiteurs = Visiteur.objects.all()
    if search:
        visiteurs = visiteurs.filter(
            Q(nom__icontains=search)
            | Q(prenom__icontains=search)
            | Q(numero_piece__icontains=search)
            | Q(piece_identite__icontains=search)
        )
    if centre_id:
        visiteurs = visiteurs.filter(visites__detenu__centre_id=centre_id)
    if detenu_id:
        visiteurs = visiteurs.filter(visites__detenu_id=detenu_id)

    visiteurs = visiteurs.annotate(
        nb_visites=Count(
            'visites',
            filter=Q(visites__statut__in=_STATUTS_PONT),
            distinct=True,
        ),
        nb_prisons=Count(
            'visites__detenu__centre',
            filter=Q(visites__statut__in=_STATUTS_PONT),
            distinct=True,
        ),
        nb_detenus=Count(
            'visites__detenu',
            filter=Q(visites__statut__in=_STATUTS_PONT),
            distinct=True,
        ),
    ).filter(nb_visites__gt=0)

    if parcours == 'multi_prisons':
        visiteurs = visiteurs.filter(nb_prisons__gt=1)
    elif parcours == 'multi_detenus':
        visiteurs = visiteurs.filter(nb_detenus__gt=1)
    elif parcours == 'multi':
        visiteurs = visiteurs.filter(Q(nb_prisons__gt=1) | Q(nb_detenus__gt=1))
    elif parcours == 'pont':
        visiteurs = visiteurs.filter(nb_prisons__gt=1, nb_detenus__gt=1)

    visiteurs = visiteurs.order_by('-nb_prisons', '-nb_detenus', 'nom', 'prenom')

    stats_base = Visiteur.objects.annotate(
        nb_visites=Count(
            'visites',
            filter=Q(visites__statut__in=_STATUTS_PONT),
            distinct=True,
        ),
        nb_prisons=Count(
            'visites__detenu__centre',
            filter=Q(visites__statut__in=_STATUTS_PONT),
            distinct=True,
        ),
        nb_detenus=Count(
            'visites__detenu',
            filter=Q(visites__statut__in=_STATUTS_PONT),
            distinct=True,
        ),
    ).filter(nb_visites__gt=0)

    visiteur_suivi = None
    visites_parcours = []
    prisons_parcours = []
    detenus_parcours = []
    est_pont = False
    relais_pont = []
    nb_relais_rapides = 0
    seuil_relais_jours = SEUIL_RELAIS_JOURS
    if visiteur_id:
        visiteur_suivi = get_object_or_404(Visiteur, pk=visiteur_id)
        visites_parcours = list(
            Visite.objects.filter(visiteur=visiteur_suivi)
            .select_related('detenu', 'detenu__centre')
            .order_by('-date_visite')
        )
        prisons_seen = {}
        detenus_seen = {}
        for visite in visites_parcours:
            centre = visite.detenu.centre
            if centre.id not in prisons_seen:
                prisons_seen[centre.id] = centre
            detenu = visite.detenu
            if detenu.id not in detenus_seen:
                detenus_seen[detenu.id] = detenu
        prisons_parcours = list(prisons_seen.values())
        detenus_parcours = list(detenus_seen.values())
        analyse_pont = _analyser_pont_communication(visites_parcours)
        est_pont = analyse_pont['est_pont']
        relais_pont = analyse_pont['relais']
        nb_relais_rapides = analyse_pont['nb_relais_rapides']
        seuil_relais_jours = analyse_pont['seuil_jours']

    paginator = Paginator(visiteurs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search': search,
        'centre_id': centre_id,
        'detenu_id': detenu_id,
        'parcours': parcours,
        'visiteur_id': visiteur_id,
        'centres': CentrePenitencier.objects.filter(statut=True).order_by('nom'),
        'detenus': Detenu.objects.select_related('centre').order_by('nom', 'prenom'),
        'total_visiteurs': stats_base.count(),
        'nb_multi_prisons': stats_base.filter(nb_prisons__gt=1).count(),
        'nb_multi_detenus': stats_base.filter(nb_detenus__gt=1).count(),
        'nb_ponts': stats_base.filter(nb_prisons__gt=1, nb_detenus__gt=1).count(),
        'nb_filtres': visiteurs.count(),
        'visiteur_suivi': visiteur_suivi,
        'visites_parcours': visites_parcours,
        'prisons_parcours': prisons_parcours,
        'detenus_parcours': detenus_parcours,
        'est_pont': est_pont,
        'relais_pont': relais_pont,
        'nb_relais_rapides': nb_relais_rapides,
        'seuil_relais_jours': seuil_relais_jours,
    }
    return render(request, 'visites/suivi_visiteur.html', context)

