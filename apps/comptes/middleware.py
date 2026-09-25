from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


CONSULTATION_MSG = (
    "Mode consultation : l'administrateur central ne peut pas modifier "
    "les données des prisons."
)

_WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
_ALLOWED_WRITE_PREFIXES = (
    '/logout/',
    '/accounts/logout/',
    '/centres/creer/',
    '/admins-prison/creer/',
)


def _is_centre_write(path, method):
    """Création / modification des prisons par l'admin central."""
    if method == 'POST' and path.rstrip('/') == '/api/detenus/centres':
        return True
    if '/modifier/' in path and (
        path.startswith('/centres/')
        or path.startswith('/api/detenus/web/centres/')
    ):
        return True
    stripped = path.rstrip('/')
    if stripped.startswith('/api/detenus/centres/') and stripped != '/api/detenus/centres':
        return method in {'PUT', 'PATCH', 'DELETE'}
    return False


def _is_admin_prison_write(path, method):
    """Création / mise à jour des administrateurs de prison par l'admin central."""
    if method == 'POST' and path.rstrip('/') == '/api/detenus/admins-prison':
        return True
    if path.startswith('/api/detenus/web/admins-prison/') and (
        '/modifier/' in path or '/toggle-status/' in path
    ):
        return True
    return False


class AdminCentralConsultationMiddleware:
    """Bloque les écritures opérationnelles, sauf création de prisons et d'admins."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (
            user is not None
            and user.is_authenticated
            and getattr(user, 'is_admin_central', lambda: False)()
            and request.method in _WRITE_METHODS
        ):
            path = request.path
            allowed = (
                any(path.startswith(prefix) for prefix in _ALLOWED_WRITE_PREFIXES)
                or _is_centre_write(path, request.method)
                or _is_admin_prison_write(path, request.method)
            )
            if not allowed:
                wants_json = (
                    path.startswith('/api/')
                    or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    or 'application/json' in (request.headers.get('Accept') or '')
                )
                if wants_json:
                    return JsonResponse(
                        {'success': False, 'error': CONSULTATION_MSG},
                        status=403,
                    )
                messages.error(request, CONSULTATION_MSG)
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    return redirect(referer)
                return redirect('dashboard_central')
        return self.get_response(request)


class RoleBasedRedirectMiddleware:
    """
    Middleware pour rediriger les utilisateurs selon leur rôle après la connexion
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ne pas appliquer la redirection pour les URLs statiques, login/logout, ou API endpoints
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/admin/') or
            request.path == '/' or
            request.path == '/login/' or
            request.path == '/logout/' or
            request.path == '/accounts/login/' or
            request.path.startswith('/api/detenus/admins-prison/') or
            request.path.startswith('/api/detenus/centres/') or
            request.path.startswith('/api/detenus/detenus/') or
            request.path.startswith('/centres/') or
            request.path.startswith('/admins-prison/') or
            # URLs pour les admins de centre
            request.path.startswith('/api/detenus/web/') or
            request.path.startswith('/api/visites/web/') or
            request.path.startswith('/api/personnel/web/') or
            request.path.startswith('/detenus/') or
            request.path.startswith('/visites/') or
            request.path.startswith('/suivi-visiteur/') or
            request.path.startswith('/personnel/') or
            request.path.startswith('/visiteurs/') or
            request.path.startswith('/surveillance/')):
            return self.get_response(request)
        
        # Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            # Rediriger l'admin central vers son dashboard
            if request.user.is_admin_central():
                # Ne pas rediriger s'il est déjà sur son dashboard ou sur les pages de gestion
                if (not request.path.startswith('/api/detenus/web/dashboard-central/') and
                    not request.path.startswith('/api/detenus/web/centres/') and
                    not request.path.startswith('/api/detenus/web/admins-prison/') and
                    not request.path.startswith('/centres/') and
                    not request.path.startswith('/admins-prison/') and
                    not request.path.startswith('/suivi-visiteur/')):
                    return redirect('/api/detenus/web/dashboard-central/')
            
            # Rediriger les admins de centre vers le dashboard général
            elif hasattr(request.user, 'adminprison'):
                # Ne pas rediriger s'il est déjà sur le dashboard ou sur les pages de gestion
                if (not request.path.startswith('/dashboard/') and
                    not request.path.startswith('/api/detenus/web/') and
                    not request.path.startswith('/api/visites/web/') and
                    not request.path.startswith('/api/personnel/web/') and
                    not request.path.startswith('/detenus/') and
                    not request.path.startswith('/visites/') and
                    not request.path.startswith('/personnel/') and
                    not request.path.startswith('/visiteurs/') and
                    not request.path.startswith('/surveillance/')):
                    return redirect('/dashboard/')
        
        return self.get_response(request)
