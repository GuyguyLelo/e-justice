from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Visiteur, Visite, ObjetVisite, TypeVisiteur, StatutVisite
from .forms import VisiteurForm, VisiteForm, ObjetVisiteForm
from apps.comptes.models import Utilisateur
from apps.detenus.models import Detenu


@login_required
def visiteurs_list_view(request):
    """Liste des visiteurs avec recherche et filtrage"""
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
    visiteur = get_object_or_404(Visiteur, id=visiteur_id)
    
    # Visites du visiteur
    visites = visiteur.visites.all().order_by('-date_visite')[:10]
    
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
        form = VisiteurForm(request.POST)
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
        form = VisiteurForm(request.POST, instance=visiteur)
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
    
    # Récupérer les paramètres de recherche
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    detenu_id = request.GET.get('detenu', '')
    date_filter = request.GET.get('date', 'today')  # Filtre de période
    custom_date = request.GET.get('custom_date', '')  # Date personnalisée
    
    # Construire la requête de base selon le rôle de l'utilisateur
    user = request.user
    if user.is_admin_central():
        # L'admin central voit toutes les visites
        visites = Visite.objects.all()
    elif hasattr(user, 'adminprison'):
        # L'admin de centre ne voit que les visites des détenus de son centre
        visites = Visite.objects.filter(detenu__centre=user.adminprison.centre)
    else:
        # Autres rôles ne voient rien
        visites = Visite.objects.none()
    
    # Trier
    visites = visites.order_by('-date_visite')
    
    # Filtrer par date
    if custom_date:
        # Utiliser la date personnalisée
        try:
            from datetime import datetime
            date_obj = datetime.strptime(custom_date, '%Y-%m-%d').date()
            visites = visites.filter(date_visite__date=date_obj)
        except ValueError:
            # Si la date est invalide, utiliser aujourd'hui
            aujourd_hui = timezone.now().date()
            visites = visites.filter(date_visite__date=aujourd_hui)
    elif date_filter == 'today':
        aujourd_hui = timezone.now().date()
        visites = visites.filter(date_visite__date=aujourd_hui)
    elif date_filter == 'week':
        debut_semaine = timezone.now().date() - timezone.timedelta(days=7)
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
        'detenus': Detenu.objects.all().order_by('nom', 'prenom'),
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
    visite = get_object_or_404(Visite, id=visite_id)
    
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

