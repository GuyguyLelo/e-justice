from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Personnel, FormationPersonnel, SanctionPersonnel, TypePersonnel, StatutPersonnel
from .forms import PersonnelForm, FormationPersonnelForm, SanctionPersonnelForm
from apps.comptes.models import Utilisateur


@login_required
def personnel_list_view(request):
    """Liste du personnel avec recherche et filtrage"""
    # Récupérer les paramètres de recherche
    search = request.GET.get('search', '')
    type_personnel = request.GET.get('type_personnel', '')
    statut = request.GET.get('statut', '')
    
    # Construire la requête de base selon le rôle de l'utilisateur
    user = request.user
    if user.is_admin_central():
        # L'admin central voit tout le personnel
        personnel = Personnel.objects.all()
    elif hasattr(user, 'adminprison'):
        # L'admin de centre voit le personnel de son centre
        personnel = Personnel.objects.filter(centre=user.adminprison.centre)
    else:
        # Autres rôles ne voient rien
        personnel = Personnel.objects.none()
    
    # Trier
    personnel = personnel.order_by('nom', 'prenom')
    
    # Appliquer les filtres
    if search:
        personnel = personnel.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(matricule__icontains=search) |
            Q(specialite__icontains=search)
        )
    
    if type_personnel:
        personnel = personnel.filter(type_personnel=type_personnel)
    
    if statut:
        personnel = personnel.filter(statut=statut)
    
    # Pagination
    paginator = Paginator(personnel, 20)  # 20 membres du personnel par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_personnel': personnel.count(),
        'nb_actifs': personnel.filter(statut=StatutPersonnel.ACTIF).count(),
        'nb_conge': personnel.filter(statut=StatutPersonnel.CONGE).count(),
        'nb_inactifs': personnel.filter(statut=StatutPersonnel.INACTIF).count(),
        'types_personnel': TypePersonnel.choices,
        'statuts': StatutPersonnel.choices,
        'user_centre': user.adminprison.centre if hasattr(user, 'adminprison') else None,
    }
    
    return render(request, 'personnel/personnel_list.html', context)


@login_required
def personnel_detail_view(request, personnel_id):
    """Détail d'un membre du personnel"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    
    # Formations du personnel
    formations = personnel.formations.all().order_by('-date_debut')[:10]
    
    # Sanctions du personnel
    sanctions = personnel.sanctions.all().order_by('-date_sanction')[:10]
    
    context = {
        'personnel': personnel,
        'formations': formations,
        'sanctions': sanctions,
        'personnel_full_name': personnel.nom_complet,
    }
    
    return render(request, 'personnel/personnel_detail.html', context)


@login_required
def personnel_create_view(request):
    """Création d'un nouveau membre du personnel"""
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_personnel():
        messages.error(request, "Vous n'avez pas la permission de créer du personnel.")
        return redirect('personnel_list')
    
    if request.method == 'POST':
        form = PersonnelForm(request.POST)
        if form.is_valid():
            personnel = form.save()
            # Assigner le centre si admin de centre
            if hasattr(request.user, 'adminprison'):
                personnel.centre = request.user.adminprison.centre
                personnel.save()
            messages.success(request, f'Personnel {personnel.nom_complet} créé avec succès.')
            return redirect('personnel_detail', personnel_id=personnel.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PersonnelForm()
        # Pré-remplir le centre pour les admins de centre
        if hasattr(request.user, 'adminprison'):
            form.initial['centre'] = request.user.adminprison.centre
    
    context = {
        'form': form,
        'title': 'Nouveau membre du personnel',
        'action': 'Créer',
        'user_centre': request.user.adminprison.centre if hasattr(request.user, 'adminprison') else None,
        'can_edit': user.can_edit_personnel(),
    }
    
    return render(request, 'personnel/personnel_form.html', context)


@login_required
def personnel_edit_view(request, personnel_id):
    """Modification d'un membre du personnel"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_personnel():
        messages.error(request, "Vous n'avez pas la permission de modifier le personnel.")
        return redirect('personnel_detail', personnel_id=personnel.id)
    
    # Vérifier que l'admin de centre ne modifie que le personnel de son centre
    if hasattr(user, 'adminprison'):
        centre_users_ids = Utilisateur.objects.filter(
            adminprison__centre=user.adminprison.centre
        ).values_list('id', flat=True)
        if personnel.utilisateur_id not in centre_users_ids:
            messages.error(request, "Vous n'avez pas la permission de modifier ce membre du personnel.")
            return redirect('personnel_detail', personnel_id=personnel.id)
    
    if request.method == 'POST':
        form = PersonnelForm(request.POST, instance=personnel, user=request.user)
        if form.is_valid():
            personnel = form.save()
            messages.success(request, f'Personnel {personnel.utilisateur.get_full_name} modifié avec succès.')
            return redirect('personnel_detail', personnel_id=personnel.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PersonnelForm(instance=personnel, user=request.user)
    
    context = {
        'form': form,
        'personnel': personnel,
        'title': f'Modifier {personnel.utilisateur.get_full_name}',
        'action': 'Modifier',
        'can_edit': user.can_edit_personnel(),
    }
    
    return render(request, 'personnel/personnel_form.html', context)


@login_required
def personnel_delete_view(request, personnel_id):
    """Suppression d'un membre du personnel"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    
    # Vérifier les permissions
    user = request.user
    if not user.can_edit_personnel():
        messages.error(request, "Vous n'avez pas la permission de supprimer du personnel.")
        return redirect('personnel_detail', personnel_id=personnel.id)
    
    # Vérifier que l'admin de centre ne supprime que le personnel de son centre
    if hasattr(user, 'adminprison'):
        centre_users_ids = Utilisateur.objects.filter(
            adminprison__centre=user.adminprison.centre
        ).values_list('id', flat=True)
        if personnel.utilisateur_id not in centre_users_ids:
            messages.error(request, "Vous n'avez pas la permission de supprimer ce membre du personnel.")
            return redirect('personnel_detail', personnel_id=personnel.id)
    
    if request.method == 'POST':
        personnel.delete()
        messages.success(request, 'Membre du personnel supprimé avec succès.')
        return redirect('personnel_list')
    
    context = {
        'personnel': personnel,
        'can_edit': user.can_edit_personnel(),
    }
    
    return render(request, 'personnel/personnel_confirm_delete.html', context)


# Gestion des formations
@login_required
def formation_create_view(request, personnel_id):
    """Ajouter une formation à un membre du personnel"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    
    if request.method == 'POST':
        form = FormationPersonnelForm(request.POST)
        if form.is_valid():
            formation = form.save(commit=False)
            formation.personnel = personnel
            formation.save()
            messages.success(request, 'Formation ajoutée avec succès.')
            return redirect('personnel_detail', personnel_id=personnel.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = FormationPersonnelForm()
    
    context = {
        'form': form,
        'personnel': personnel,
        'title': f'Ajouter une formation à {personnel.utilisateur.get_full_name}',
        'action': 'Ajouter'
    }
    
    return render(request, 'personnel/formation_form.html', context)


# Gestion des sanctions
@login_required
def sanction_create_view(request, personnel_id):
    """Ajouter une sanction à un membre du personnel"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    
    if request.method == 'POST':
        form = SanctionPersonnelForm(request.POST)
        if form.is_valid():
            sanction = form.save(commit=False)
            sanction.personnel = personnel
            sanction.save()
            messages.success(request, 'Sanction ajoutée avec succès.')
            return redirect('personnel_detail', personnel_id=personnel.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = SanctionPersonnelForm()
    
    context = {
        'form': form,
        'personnel': personnel,
        'title': f'Ajouter une sanction à {personnel.utilisateur.get_full_name}',
        'action': 'Ajouter'
    }
    
    return render(request, 'personnel/sanction_form.html', context)


# API Views pour AJAX
@csrf_exempt
@require_http_methods(["GET"])
def api_personnel_search(request):
    """API de recherche de personnel pour AJAX"""
    search = request.GET.get('q', '')
    
    if len(search) < 2:
        return JsonResponse({'results': []})
    
    personnel = Personnel.objects.filter(
        Q(utilisateur__first_name__icontains=search) |
        Q(utilisateur__last_name__icontains=search) |
        Q(matricule__icontains=search)
    )[:10]
    
    results = []
    for p in personnel:
        results.append({
            'id': p.id,
            'nom_complet': p.utilisateur.get_full_name,
            'matricule': p.matricule,
            'type_personnel': p.get_type_personnel_display(),
            'statut': p.get_statut_display(),
        })
    
    return JsonResponse({'results': results})


@csrf_exempt
@require_http_methods(["POST"])
def api_personnel_action(request, personnel_id):
    """API pour actions sur un membre du personnel"""
    personnel = get_object_or_404(Personnel, id=personnel_id)
    action = request.POST.get('action')
    
    if action == 'activer':
        personnel.statut = StatutPersonnel.ACTIF
        personnel.save()
        return JsonResponse({'success': True, 'message': 'Personnel activé'})
    
    elif action == 'desactiver':
        personnel.statut = StatutPersonnel.INACTIF
        personnel.save()
        return JsonResponse({'success': True, 'message': 'Personnel désactivé'})
    
    elif action == 'mettre_conge':
        personnel.statut = StatutPersonnel.CONGE
        personnel.save()
        return JsonResponse({'success': True, 'message': 'Personnel mis en congé'})
    
    return JsonResponse({'success': False, 'message': 'Action non reconnue'})

