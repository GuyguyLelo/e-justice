from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from .forms import UtilisateurCreationForm
from .models import Utilisateur


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Bienvenue, {user.get_full_name()}!')
                
                # Redirection selon le paramètre LOGIN_REDIRECT_URL
                next_url = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
                return redirect(next_url)
            else:
                messages.error(request, 'Votre compte est désactivé.')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'auth/login.html', {
        'demo_accounts': _demo_accounts(),
    })


def _demo_accounts():
    """Comptes de démonstration connus (identifiants + mot de passe par défaut)."""
    passwords = {
        'admin_central': 'admin123',
        'admin1': 'admin123',
        'admin': 'admin123',
        'directeur': 'directeur123',
        'agent1': 'agent123',
        'medecin1': 'medecin123',
        'admin_centre_test': 'admin123',
    }
    accounts = []
    for user in Utilisateur.objects.filter(is_active=True).order_by('id'):
        password = passwords.get(user.username)
        if not password:
            continue
        centre = ''
        try:
            centre = user.adminprison.centre.nom
        except Exception:
            pass
        accounts.append({
            'username': user.username,
            'password': password,
            'role': user.get_role_display(),
            'name': user.get_full_name(),
            'centre': centre,
        })
    if accounts:
        return accounts
    return [
        {'username': 'admin_central', 'password': 'admin123', 'role': 'Administrateur Central', 'name': 'Admin Central', 'centre': ''},
        {'username': 'admin1', 'password': 'admin123', 'role': 'Administrateur', 'name': 'Administrateur centre', 'centre': ''},
    ]


def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('accueil')


@login_required
def dashboard_view(request):
    """Tableau de bord principal - Redirection selon le rôle"""
    user = request.user
    
    # Rediriger selon le rôle de l'utilisateur
    if user.is_admin_central():
        return redirect('/api/detenus/web/dashboard-central/')
    elif hasattr(user, 'adminprison'):
        # L'admin de centre reste sur le dashboard général pour l'instant
        pass
    
    # Continuer avec le dashboard normal pour les autres cas
    from django.utils import timezone
    from datetime import timedelta
    
    # Statistiques selon le rôle
    stats = {
        'user': user,
        'role': user.get_role_display(),
        'total_detenus': 0,
        'total_personnel': 0,
        'total_visites': 0,
        'total_consultations': 0,
        'visites_aujourd_hui': 0,
        'visites_en_cours': 0,
        'visites_semaine': 0,
        'visites_attente': 0,
        'visites_recentes': [],
        'detenus_recents': [],
        'alertes': 0,
        'performance': 'N/A',
        'enfants': 0,
        'enfants_incarceres': 0,
    }
    
    # Ajouter des statistiques réelles selon les permissions
    if hasattr(user, 'adminprison'):
        from apps.detenus.models import Detenu, CentrePenitencier, filtrer_enfants
        from apps.personnel.models import Personnel
        from apps.visites.models import Visite

        centre = CentrePenitencier.objects.prefetch_related('photos').get(
            pk=user.adminprison.centre_id
        )
        stats['centre'] = centre

        stats['total_detenus'] = Detenu.objects.filter(centre=centre).count()
        stats['detenus_incarceres'] = Detenu.objects.filter(centre=centre, statut='INCARCERE').count()
        stats['detenus_liberes'] = Detenu.objects.filter(centre=centre, statut='LIBERE').count()
        stats['detenus_transferes'] = Detenu.objects.filter(centre=centre, statut='TRANSFERE').count()
        stats['detenus_evades'] = Detenu.objects.filter(centre=centre, statut='EVADE').count()
        stats['detenus_decedes'] = Detenu.objects.filter(centre=centre, statut='DECEDE').count()

        stats['total_hommes'] = Detenu.objects.filter(centre=centre, sexe='M').count()
        stats['total_femmes'] = Detenu.objects.filter(centre=centre, sexe='F').count()
        stats['hommes_incarceres'] = Detenu.objects.filter(centre=centre, sexe='M', statut='INCARCERE').count()
        stats['femmes_incarceres'] = Detenu.objects.filter(centre=centre, sexe='F', statut='INCARCERE').count()
        stats['enfants'] = filtrer_enfants(Detenu.objects.filter(centre=centre)).count()
        stats['enfants_incarceres'] = filtrer_enfants(
            Detenu.objects.filter(centre=centre), incarceres=True
        ).count()

        personnel_qs = Personnel.objects.filter(centre=centre)
        stats['total_personnel'] = personnel_qs.count()
        stats['personnel_actif'] = personnel_qs.filter(statut='ACTIF').count()
        stats['personnel_inactif'] = personnel_qs.filter(statut='INACTIF').count()
        stats['personnel_conge'] = personnel_qs.filter(statut='CONGE').count()

        visites_qs = Visite.objects.filter(detenu__centre=centre)
        stats['total_visites'] = visites_qs.count()
        stats['visites_terminees'] = visites_qs.filter(statut='TERMINEE').count()
        stats['visites_en_cours'] = visites_qs.filter(statut='EN_COURS').count()
        stats['visites_programmees'] = visites_qs.filter(statut='PROGRAMMEE').count()
        stats['visites_attente'] = stats['visites_programmees']

        aujourd_hui = timezone.now().date()
        debut_semaine = aujourd_hui - timedelta(days=7)
        stats['visites_aujourd_hui'] = visites_qs.filter(date_visite__date=aujourd_hui).count()
        stats['visites_semaine'] = visites_qs.filter(date_visite__date__gte=debut_semaine).count()

        stats['visites_recentes'] = visites_qs.select_related(
            'visiteur', 'detenu'
        ).order_by('-date_visite')[:8]
        stats['detenus_recents'] = Detenu.objects.filter(centre=centre).order_by('-created_at')[:8]

        stats['capacite_max'] = centre.capacite_max
        stats['capacite_actuelle'] = centre.capacite_actuelle
        stats['places_disponibles'] = centre.places_disponibles
        stats['taux_occupation'] = centre.taux_occupation
        
    elif user.role in ['ADMIN', 'DIRECTEUR']:
        from apps.detenus.models import Detenu, CentrePenitencier, filtrer_enfants
        from apps.personnel.models import Personnel
        from apps.visites.models import Visite
        from apps.soins.models import Consultation
        
        # Statistiques globales
        stats['total_detenus'] = Detenu.objects.count()
        stats['detenus_incarceres'] = Detenu.objects.filter(statut='INCARCERE').count()
        stats['detenus_liberes'] = Detenu.objects.filter(statut='LIBERE').count()
        stats['detenus_transferes'] = Detenu.objects.filter(statut='TRANSFERE').count()
        stats['detenus_evades'] = Detenu.objects.filter(statut='EVADE').count()
        stats['detenus_decedes'] = Detenu.objects.filter(statut='DECEDE').count()
        
        # Statistiques par genre globales
        stats['total_hommes'] = Detenu.objects.filter(sexe='M').count()
        stats['total_femmes'] = Detenu.objects.filter(sexe='F').count()
        stats['hommes_incarceres'] = Detenu.objects.filter(sexe='M', statut='INCARCERE').count()
        stats['femmes_incarceres'] = Detenu.objects.filter(sexe='F', statut='INCARCERE').count()
        stats['enfants'] = filtrer_enfants(Detenu.objects.all()).count()
        stats['enfants_incarceres'] = filtrer_enfants(Detenu.objects.all(), incarceres=True).count()
        
        # Statistiques des centres
        stats['total_centres'] = CentrePenitencier.objects.count()
        stats['centres_actifs'] = CentrePenitencier.objects.filter(statut='ACTIF').count() if hasattr(CentrePenitencier, 'statut') else CentrePenitencier.objects.count()
        
        # Statistiques du personnel
        stats['total_personnel'] = Personnel.objects.count()
        stats['personnel_actif'] = Personnel.objects.filter(statut='ACTIF').count()
        stats['personnel_inactif'] = Personnel.objects.filter(statut='INACTIF').count()
        stats['personnel_conge'] = Personnel.objects.filter(statut='CONGE').count()
        
        # Statistiques des visites
        stats['total_visites'] = Visite.objects.count()
        stats['visites_terminees'] = Visite.objects.filter(statut='TERMINEE').count()
        stats['visites_en_cours'] = Visite.objects.filter(statut='EN_COURS').count()
        stats['visites_programmees'] = Visite.objects.filter(statut='PROGRAMMEE').count()
        stats['total_consultations'] = Consultation.objects.count()
        
        # Statistiques avancées
        aujourd_hui = timezone.now().date()
        debut_semaine = aujourd_hui - timedelta(days=7)
        
        stats['visites_aujourd_hui'] = Visite.objects.filter(date_visite__date=aujourd_hui).count()
        stats['visites_semaine'] = Visite.objects.filter(date_visite__date__gte=debut_semaine).count()
        stats['visites_attente'] = Visite.objects.filter(statut='PROGRAMMEE').count()
        
        # Activité récente
        stats['visites_recentes'] = Visite.objects.select_related('visiteur', 'detenu').order_by('-date_visite')[:10]
        stats['detenus_recents'] = Detenu.objects.order_by('-created_at')[:5]
        
        # Calcul de performance
        total_visites = stats['total_visites']
        visites_terminees = stats['visites_terminees']
        if total_visites > 0:
            stats['performance'] = round((visites_terminees / total_visites) * 100)
        else:
            stats['performance'] = 0
        
        # Taux d'occupation global
        total_capacity = sum([c.capacite_maximale for c in CentrePenitencier.objects.all() if hasattr(c, 'capacite_maximale') and c.capacite_maximale])
        if total_capacity > 0:
            stats['taux_occupation_global'] = round((stats['detenus_incarceres'] / total_capacity) * 100, 1)
        else:
            stats['taux_occupation_global'] = 0
    
    return render(request, 'dashboard_compact.html', stats)


@login_required
def profile_view(request):
    """Profil utilisateur"""
    if request.method == 'POST':
        # Mise à jour du profil
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.telephone = request.POST.get('telephone', user.telephone)
        user.adresse = request.POST.get('adresse', user.adresse)
        user.save()
        
        messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('profile')
    
    return render(request, 'auth/profile.html', {'user': request.user})


@login_required
def change_password_view(request):
    """Changement de mot de passe"""
    if request.method == 'POST':
        from .forms import ChangePasswordForm
        
        form = ChangePasswordForm(request.user, request.POST)
        
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            
            # Reconnecter l'utilisateur
            login(request, user)
            messages.success(request, 'Mot de passe modifié avec succès.')
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        from .forms import ChangePasswordForm
        form = ChangePasswordForm(request.user)
    
    return render(request, 'auth/change_password.html', {'form': form})


def register_view(request):
    """Inscription d'un nouvel utilisateur (admin seulement)"""
    if not request.user.is_authenticated or request.user.role != 'ADMIN':
        messages.error(request, 'Accès non autorisé.')
        return redirect('login')
    
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Utilisateur {user.username} créé avec succès.')
            return redirect('admin_users')
    else:
        form = UtilisateurCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})


@login_required
def admin_users_view(request):
    """Gestion des utilisateurs (admin seulement)"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Accès non autorisé.')
        return redirect('dashboard')
    
    users = Utilisateur.objects.all().order_by('-date_joined')
    return render(request, 'auth/admin_users.html', {'users': users})


# API Views pour AJAX
@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API de connexion pour AJAX"""
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None and user.is_active:
        login(request, user)
        return JsonResponse({
            'success': True,
            'message': 'Connexion réussie',
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'role': user.role
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Nom d\'utilisateur ou mot de passe incorrect'
        })


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """API de déconnexion pour AJAX"""
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Déconnexion réussie'
    })





