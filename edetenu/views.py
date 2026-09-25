from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def accueil_view(request):
    """Page d'accueil institutionnelle de la plateforme e-Justice."""
    fonctions = [
        {
            'code': 'Enquêtes',
            'titre': 'Police judiciaire',
            'icone': 'bi-search',
            'statut': 'prévu',
            'texte': 'Procès-verbaux, scellés, interpellations et transmission au parquet.',
        },
        {
            'code': 'Parquet',
            'titre': 'Poursuites publiques',
            'icone': 'bi-briefcase',
            'statut': 'prévu',
            'texte': 'Ouverture des dossiers, classements, réquisitoires et orientation des affaires.',
        },
        {
            'code': 'Instruction',
            'titre': 'Instruction préparatoire',
            'icone': 'bi-folder2-open',
            'statut': 'prévu',
            'texte': 'Mandats, commissions rogatoires et suivi du dossier d’instruction.',
        },
        {
            'code': 'Greffe',
            'titre': 'Audiences et greffe',
            'icone': 'bi-bank',
            'statut': 'prévu',
            'texte': 'Rôle d’audience, convocations, minutes et archives des juridictions.',
        },
        {
            'code': 'Décisions',
            'titre': 'Jugements et arrêts',
            'icone': 'bi-pen',
            'statut': 'prévu',
            'texte': 'Rédaction, signification, voies de recours et exécution des décisions.',
        },
        {
            'code': 'Casier',
            'titre': 'Casier judiciaire',
            'icone': 'bi-journal-text',
            'statut': 'prévu',
            'texte': 'Mentions pénales, extraits, réhabilitation et communication aux autorités.',
        },
        {
            'code': 'e-Detenu',
            'titre': 'Exécution des peines',
            'icone': 'bi-person-badge',
            'statut': 'opérationnel',
            'lien': 'login',
            'texte': 'Centres, fiches, dossiers, visites, personnel et surveillance.',
        },
        {
            'code': 'Civil',
            'titre': 'Justice civile',
            'icone': 'bi-balance-scale',
            'statut': 'prévu',
            'texte': 'Assignations, référés, état civil judiciaire et contentieux commercial.',
        },
        {
            'code': 'Aide',
            'titre': 'Aide juridictionnelle',
            'icone': 'bi-life-preserver',
            'statut': 'prévu',
            'texte': 'Demandes d’aide, commission d’office et suivi du barreau.',
        },
        {
            'code': 'Pilotage',
            'titre': 'Statistiques nationales',
            'icone': 'bi-graph-up',
            'statut': 'prévu',
            'texte': 'Indicateurs, délais de justice, occupation des centres et tableaux de bord.',
        },
    ]
    return render(request, 'accueil.html', {'fonctions': fonctions})


@csrf_exempt
@require_http_methods(["GET"])
def api_info(request):
    """Vue d'accueil pour l'API e-Detenu"""
    return JsonResponse({
        'message': 'Bienvenue sur l\'API e-Detenu',
        'version': '1.0.0',
        'description': 'Système de gestion des centres pénitentiaires en RDC',
        'endpoints': {
            'documentation': '/api/docs/',
            'authentification': '/api/auth/auth/login/',
            'détenus': '/api/detenus/detenus/',
            'personnel': '/api/personnel/personnel/',
            'visites': '/api/visites/visites/',
            'soins': '/api/soins/consultations/',
            'logistique': '/api/logistique/produits/',
            'rapports': '/api/rapports/rapports/'
        },
        'status': 'active'
    })






