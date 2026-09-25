from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Detenu, HistoriqueDetenu, StatutDetenu, TypePeine, CentrePenitencier, AdminPrison, TypeCentre
from .serializers import (
    DetenuSerializer, DetenuListSerializer, DetenuDetailSerializer,
    HistoriqueDetenuSerializer, DetenuStatsSerializer, LiberationSerializer,
    TransfertSerializer, StatutDetenuSerializer, TypePeineSerializer,
    CentrePenitencierSerializer, CentrePenitencierListSerializer,
    AdminPrisonSerializer, AdminPrisonListSerializer, TypeCentreSerializer,
    CentreStatsSerializer
)


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def biometric_update_view(request, pk=None):
    """Vue API dédiée pour la mise à jour des données biométriques"""
    print(f"=== VUE BIOMETRIC UPDATE ===")
    print(f"Request method: {request.method}")
    print(f"Request data: {request.data}")
    print(f"Request FILES: {request.FILES}")
    
    try:
        detenu = Detenu.objects.get(id=pk)
        print(f"Détenu trouvé: {detenu.id} - {detenu.nom_complet}")
    except Detenu.DoesNotExist:
        print(f"Détenu {pk} non trouvé")
        return Response(
            {"error": "Détenu non trouvé"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Seules les données biométriques peuvent être mises à jour
    allowed_fields = ['photo_face', 'photo_profil', 'empreintes_digitales', 'adn']
    
    # Créer un historique avant modification
    old_data = {}
    for field in allowed_fields:
        old_data[field] = getattr(detenu, field)
    
    # Gérer les fichiers uploadés
    if 'photo_face' in request.FILES:
        detenu.photo_face = request.FILES['photo_face']
        print(f"Photo de face uploadée: {request.FILES['photo_face']}")
    if 'photo_profil' in request.FILES:
        detenu.photo_profil = request.FILES['photo_profil']
        print(f"Photo de profil uploadée: {request.FILES['photo_profil']}")
    
    # Mettre à jour les autres champs
    for field in allowed_fields:
        if field in request.data:
            setattr(detenu, field, request.data[field])
            print(f"Champ {field} mis à jour: {request.data[field]}")
    
    try:
        detenu.save()
        print(f"Détenu {detenu.id} sauvegardé avec succès")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du détenu: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Erreur lors de la sauvegarde: {str(e)}"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Créer l'historique des modifications biométriques
    for field in allowed_fields:
        old_value = old_data.get(field)
        new_value = getattr(detenu, field)
        
        if old_value != new_value:
            HistoriqueDetenu.objects.create(
                detenu=detenu,
                action=f'Modification biométrique {field}',
                ancienne_valeur=str(old_value) if old_value else 'None',
                nouvelle_valeur=str(new_value) if new_value else 'None',
                utilisateur=request.user
            )
            print(f"Historique créé pour {field}: {old_value} -> {new_value}")
    
    serializer = DetenuDetailSerializer(detenu)
    print(f"=== FIN VUE BIOMETRIC UPDATE ===")
    return Response(serializer.data)


class DetenuViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des détenus
    """
    queryset = Detenu.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return DetenuListSerializer
        elif self.action == 'retrieve':
            return DetenuDetailSerializer
        return DetenuSerializer
    
    def get_queryset(self):
        """Filtre les détenus selon les permissions"""
        queryset = Detenu.objects.all()
        
        # Filtres par paramètres de requête
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        regime = self.request.query_params.get('regime')
        if regime:
            queryset = queryset.filter(regime=regime)
        
        sexe = self.request.query_params.get('sexe')
        if sexe:
            queryset = queryset.filter(sexe=sexe)
        
        # Recherche par nom, prénom ou matricule
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(matricule__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Création d'un détenu avec l'utilisateur connecté comme créateur"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Mise à jour d'un détenu avec historique"""
        detenu = self.get_object()
        old_data = {
            'nom': detenu.nom,
            'prenom': detenu.prenom,
            'cellule': detenu.cellule,
            'statut': detenu.statut,
        }
        
        serializer.save()
        
        # Créer un historique des modifications
        new_data = serializer.validated_data
        for field, new_value in new_data.items():
            if field in old_data and old_data[field] != new_value:
                HistoriqueDetenu.objects.create(
                    detenu=detenu,
                    action=f'Modification {field}',
                    ancienne_valeur=str(old_data[field]),
                    nouvelle_valeur=str(new_value),
                    utilisateur=self.request.user
                )
    
    def update(self, request, *args, **kwargs):
        """Mise à jour partielle pour les données biométriques (contournée)"""
        print(f"=== DÉBUT UPDATE ===")
        print(f"Request method: {request.method}")
        print(f"Request data: {request.data}")
        print(f"Request FILES: {request.FILES}")
        print(f"Request headers: {dict(request.headers)}")
        
        detenu = self.get_object()
        print(f"Détenu trouvé: {detenu.id} - {detenu.nom_complet}")
        
        # Seules les données biométriques peuvent être mises à jour via cette méthode
        allowed_fields = ['photo_face', 'photo_profil', 'empreintes_digitales', 'adn']
        print(f"Champs autorisés: {allowed_fields}")
        
        # Créer un historique avant modification
        old_data = {}
        for field in allowed_fields:
            old_data[field] = getattr(detenu, field)
        print(f"Données originales: {old_data}")
        
        # Gérer les fichiers uploadés
        if 'photo_face' in request.FILES:
            detenu.photo_face = request.FILES['photo_face']
            print(f"Photo de face uploadée: {request.FILES['photo_face']}")
        if 'photo_profil' in request.FILES:
            detenu.photo_profil = request.FILES['photo_profil']
            print(f"Photo de profil uploadée: {request.FILES['photo_profil']}")
        
        # Mettre à jour les autres champs
        for field in allowed_fields:
            if field in request.data:
                setattr(detenu, field, request.data[field])
                print(f"Champ {field} mis à jour: {request.data[field]}")
        
        try:
            detenu.save()
            print(f"Détenu {detenu.id} sauvegardé avec succès")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du détenu: {e}")
            print(f"Type d'erreur: {type(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Erreur lors de la sauvegarde: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Créer l'historique des modifications biométriques
        for field in allowed_fields:
            old_value = old_data.get(field)
            new_value = getattr(detenu, field)
            
            if old_value != new_value:
                HistoriqueDetenu.objects.create(
                    detenu=detenu,
                    action=f'Modification biométrique {field}',
                    ancienne_valeur=str(old_value) if old_value else 'None',
                    nouvelle_valeur=str(new_value) if new_value else 'None',
                    utilisateur=request.user
                )
                print(f"Historique créé pour {field}: {old_value} -> {new_value}")
        
        serializer = DetenuDetailSerializer(detenu)
        print(f"=== FIN UPDATE ===")
        print(f"Serializer data: {serializer.data}")
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def liberer(self, request, pk=None):
        """Libère un détenu"""
        detenu = self.get_object()
        serializer = LiberationSerializer(data=request.data, context={'detenu': detenu})
        
        if serializer.is_valid():
            detenu.statut = StatutDetenu.LIBERE
            detenu.date_liberation_effective = serializer.validated_data['date_liberation']
            detenu.motif_liberation = serializer.validated_data['motif_liberation']
            detenu.save()
            
            # Créer un historique
            HistoriqueDetenu.objects.create(
                detenu=detenu,
                action='Libération',
                ancienne_valeur=StatutDetenu.INCARCERE,
                nouvelle_valeur=StatutDetenu.LIBERE,
                utilisateur=request.user
            )
            
            return Response({'message': 'Détenu libéré avec succès.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def transferer(self, request, pk=None):
        """Transfère un détenu"""
        detenu = self.get_object()
        serializer = TransfertSerializer(data=request.data, context={'detenu': detenu})
        
        if serializer.is_valid():
            detenu.statut = StatutDetenu.TRANSFERE
            detenu.save()
            
            # Créer un historique
            HistoriqueDetenu.objects.create(
                detenu=detenu,
                action='Transfert',
                ancienne_valeur=StatutDetenu.INCARCERE,
                nouvelle_valeur=f"Transféré vers {serializer.validated_data['destination']}",
                utilisateur=request.user
            )
            
            return Response({'message': 'Détenu transféré avec succès.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        """Retourne l'historique d'un détenu"""
        detenu = self.get_object()
        historique = detenu.historique.all()
        serializer = HistoriqueDetenuSerializer(historique, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des détenus"""
        queryset = self.get_queryset()
        
        # Statistiques générales
        stats = {
            'total': queryset.count(),
            'incarceres': queryset.filter(statut=StatutDetenu.INCARCERE).count(),
            'liberes': queryset.filter(statut=StatutDetenu.LIBERE).count(),
            'transferes': queryset.filter(statut=StatutDetenu.TRANSFERE).count(),
            'evades': queryset.filter(statut=StatutDetenu.EVADE).count(),
            'decedes': queryset.filter(statut=StatutDetenu.DECEDE).count(),
        }
        
        # Statistiques par sexe
        stats['par_sexe'] = {
            'Masculin': queryset.filter(sexe='M').count(),
            'Féminin': queryset.filter(sexe='F').count(),
        }
        
        # Statistiques par âge
        now = timezone.now().date()
        stats['par_age'] = {
            '18-25': queryset.filter(date_naissance__gte=now.replace(year=now.year-25),
                                   date_naissance__lt=now.replace(year=now.year-18)).count(),
            '26-35': queryset.filter(date_naissance__gte=now.replace(year=now.year-35),
                                   date_naissance__lt=now.replace(year=now.year-26)).count(),
            '36-50': queryset.filter(date_naissance__gte=now.replace(year=now.year-50),
                                   date_naissance__lt=now.replace(year=now.year-36)).count(),
            '50+': queryset.filter(date_naissance__lt=now.replace(year=now.year-50)).count(),
        }
        
        # Statistiques par régime
        stats['par_regime'] = {}
        for regime_value, regime_label in TypePeine.choices:
            stats['par_regime'][regime_label] = queryset.filter(regime=regime_value).count()
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def statuts(self, request):
        """Retourne la liste des statuts disponibles"""
        statuts = StatutDetenuSerializer.get_statuts()
        return Response(statuts)
    
    @action(detail=False, methods=['get'])
    def types_peine(self, request):
        """Retourne la liste des types de peines disponibles"""
        types_peine = TypePeineSerializer.get_types_peine()
        return Response(types_peine)
    
    @action(detail=False, methods=['get'])
    def liberation_prevue(self, request):
        """Retourne les détenus avec libération prévue dans les 30 prochains jours"""
        date_limite = timezone.now().date() + timedelta(days=30)
        detenus = self.get_queryset().filter(
            statut=StatutDetenu.INCARCERE,
            date_liberation_prevue__lte=date_limite,
            date_liberation_prevue__isnull=False
        )
        serializer = DetenuListSerializer(detenus, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def detention_longue(self, request):
        """Retourne les détenus en détention depuis plus d'un an"""
        date_limite = timezone.now().date() - timedelta(days=365)
        detenus = self.get_queryset().filter(
            statut=StatutDetenu.INCARCERE,
            date_incarceration__lte=date_limite
        )
        serializer = DetenuListSerializer(detenus, many=True)
        return Response(serializer.data)


class CentrePenitencierViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des centres pénitenciers
    """
    queryset = CentrePenitencier.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return CentrePenitencierListSerializer
        return CentrePenitencierSerializer
    
    def get_queryset(self):
        """Filtre les centres selon les permissions"""
        user = self.request.user
        queryset = CentrePenitencier.objects.all()
        
        # Si l'utilisateur est un admin de prison, il ne voit que son centre
        if hasattr(user, 'adminprison'):
            queryset = queryset.filter(id=user.adminprison.centre.id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des centres"""
        centres = self.get_queryset()
        
        stats = {
            'total_centres': centres.count(),
            'centres_actifs': centres.filter(statut=True).count(),
            'capacite_totale': centres.aggregate(total=models.Sum('capacite_max'))['total'] or 0,
            'capacite_utilisee': centres.aggregate(total=models.Sum('capacite_actuelle'))['total'] or 0,
            'places_disponibles_totales': sum(centre.places_disponibles for centre in centres),
        }
        
        # Calcul du taux d'occupation global
        if stats['capacite_totale'] > 0:
            stats['taux_occupation_global'] = (stats['capacite_utilisee'] / stats['capacite_totale']) * 100
        else:
            stats['taux_occupation_global'] = 0
        
        # Statistiques par type de centre
        stats['par_type_centre'] = {}
        for type_centre in TypeCentre.values:
            centres_type = centres.filter(type_centre=type_centre)
            stats['par_type_centre'][type_centre] = {
                'total': centres_type.count(),
                'capacite_totale': centres_type.aggregate(total=models.Sum('capacite_max'))['total'] or 0,
                'capacite_utilisee': centres_type.aggregate(total=models.Sum('capacite_actuelle'))['total'] or 0,
            }
        
        # Centres les plus chargés
        centres_plus_charges = centres.order_by('-taux_occupation')[:5]
        stats['centres_plus_charges'] = [
            {
                'nom': centre.nom,
                'taux_occupation': centre.taux_occupation,
                'capacite_max': centre.capacite_max,
                'capacite_actuelle': centre.capacite_actuelle
            }
            for centre in centres_plus_charges
        ]
        
        serializer = CentreStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def detenus(self, request, pk=None):
        """Retourne les détenus d'un centre spécifique"""
        centre = self.get_object()
        detenus = Detenu.objects.filter(centre=centre)
        serializer = DetenuListSerializer(detenus, many=True)
        return Response(serializer.data)


class AdminPrisonViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des administrateurs de prison
    """
    queryset = AdminPrison.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return AdminPrisonListSerializer
        return AdminPrisonSerializer
    
    def get_queryset(self):
        """Filtre les admins selon les permissions"""
        user = self.request.user
        queryset = AdminPrison.objects.select_related('utilisateur', 'centre')
        
        # Si l'utilisateur est un admin de prison, il ne voit que les admins de son centre
        if hasattr(user, 'adminprison'):
            queryset = queryset.filter(centre=user.adminprison.centre)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def par_centre(self, request):
        """Retourne les admins groupés par centre"""
        centres = CentrePenitencier.objects.all()
        result = {}
        
        for centre in centres:
            admins = self.get_queryset().filter(centre=centre)
            result[centre.nom] = AdminPrisonListSerializer(admins, many=True).data
        
        return Response(result)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_test_data_view(request):
    """Vue API pour créer des données de test"""
    try:
        from django.contrib.auth.models import User
        from datetime import date
        
        # Créer un centre test
        centre, created = CentrePenitencier.objects.get_or_create(
            code='TEST001',
            defaults={
                'nom': 'Centre Test',
                'type_centre': TypeCentre.PRISON,
                'adresse': 'Adresse Test',
                'capacite_max': 100,
                'capacite_actuelle': 50,
                'directeur': 'Directeur Test',
                'date_ouverture': date(2020, 1, 1),
                'statut': True
            }
        )
        
        # Créer un utilisateur test
        user, created = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'Test',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
        
        # Créer un admin de prison test
        admin, created = AdminPrison.objects.get_or_create(
            utilisateur=user,
            defaults={
                'centre': centre,
                'matricule_admin': 'TEST001',
                'poste': 'Administrateur Test',
                'date_affectation': date(2023, 1, 1),
                'statut': True
            }
        )
        
        return Response({
            'success': True,
            'message': 'Données de test créées avec succès!'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)