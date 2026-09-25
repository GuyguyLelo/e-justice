from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Consultation, Medicament, Prescription, AntecedentMedical, Vaccination,
    TypeConsultation, StatutConsultation, TypeMedicament
)
from .serializers import (
    ConsultationSerializer, ConsultationListSerializer, ConsultationDetailSerializer,
    ConsultationCreateSerializer, MedicamentSerializer, MedicamentListSerializer,
    PrescriptionSerializer, AntecedentMedicalSerializer, VaccinationSerializer,
    MedicamentStatsSerializer, ConsultationStatsSerializer, TypeConsultationSerializer,
    StatutConsultationSerializer, TypeMedicamentSerializer
)


class MedicamentViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des médicaments"""
    queryset = Medicament.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MedicamentListSerializer
        return MedicamentSerializer
    
    def get_queryset(self):
        queryset = Medicament.objects.all()
        
        type_medicament = self.request.query_params.get('type_medicament')
        if type_medicament:
            queryset = queryset.filter(type_medicament=type_medicament)
        
        stock_faible = self.request.query_params.get('stock_faible')
        if stock_faible == 'true':
            queryset = queryset.filter(stock_actuel__lte=F('stock_minimum'))
        
        expire = self.request.query_params.get('expire')
        if expire == 'true':
            from datetime import date
            queryset = queryset.filter(date_expiration__lt=date.today())
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(nom_commercial__icontains=search)
            )
        
        return queryset.order_by('nom')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        valeur_stock = queryset.aggregate(
            total=Sum(F('stock_actuel') * F('prix_unitaire'))
        )['total'] or 0
        
        stats = {
            'total': queryset.count(),
            'stock_faible': queryset.filter(stock_actuel__lte=F('stock_minimum')).count(),
            'expires': queryset.filter(date_expiration__lt=timezone.now().date()).count(),
            'valeur_stock': valeur_stock,
        }
        
        stats['par_type'] = {}
        for type_value, type_label in TypeMedicament.choices:
            stats['par_type'][type_label] = queryset.filter(type_medicament=type_value).count()
        
        return Response(stats)


class ConsultationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des consultations"""
    queryset = Consultation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ConsultationListSerializer
        elif self.action == 'retrieve':
            return ConsultationDetailSerializer
        elif self.action == 'create':
            return ConsultationCreateSerializer
        return ConsultationSerializer
    
    def get_queryset(self):
        queryset = Consultation.objects.all()
        
        type_consultation = self.request.query_params.get('type_consultation')
        if type_consultation:
            queryset = queryset.filter(type_consultation=type_consultation)
        
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        detenu_id = self.request.query_params.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        medecin_id = self.request.query_params.get('medecin')
        if medecin_id:
            queryset = queryset.filter(medecin_id=medecin_id)
        
        urgence = self.request.query_params.get('urgence')
        if urgence == 'true':
            queryset = queryset.filter(urgence=True)
        
        date_debut = self.request.query_params.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_consultation__date__gte=date_debut)
        
        date_fin = self.request.query_params.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_consultation__date__lte=date_fin)
        
        return queryset.order_by('-date_consultation')
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def commencer(self, request, pk=None):
        consultation = self.get_object()
        if consultation.statut != StatutConsultation.PROGRAMMEE:
            return Response(
                {'error': 'Cette consultation ne peut pas être commencée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.statut = StatutConsultation.EN_COURS
        consultation.medecin = request.user
        consultation.save()
        
        return Response({'message': 'Consultation commencée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        consultation = self.get_object()
        if consultation.statut != StatutConsultation.EN_COURS:
            return Response(
                {'error': 'Cette consultation n\'est pas en cours.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.diagnostic = request.data.get('diagnostic', consultation.diagnostic)
        consultation.traitement_prescrit = request.data.get('traitement_prescrit', consultation.traitement_prescrit)
        consultation.recommandations = request.data.get('recommandations', consultation.recommandations)
        consultation.date_controle = request.data.get('date_controle')
        
        consultation.statut = StatutConsultation.TERMINEE
        consultation.save()
        
        return Response({'message': 'Consultation terminée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        consultation = self.get_object()
        if consultation.statut in [StatutConsultation.TERMINEE, StatutConsultation.ANNULEE]:
            return Response(
                {'error': 'Cette consultation ne peut pas être annulée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.statut = StatutConsultation.ANNULEE
        consultation.save()
        
        return Response({'message': 'Consultation annulée avec succès.'})
    
    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        consultation = self.get_object()
        prescriptions = consultation.prescriptions.all()
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ajouter_prescription(self, request, pk=None):
        consultation = self.get_object()
        serializer = PrescriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(consultation=consultation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'programmees': queryset.filter(statut=StatutConsultation.PROGRAMMEE).count(),
            'en_cours': queryset.filter(statut=StatutConsultation.EN_COURS).count(),
            'terminees': queryset.filter(statut=StatutConsultation.TERMINEE).count(),
            'annulees': queryset.filter(statut=StatutConsultation.ANNULEE).count(),
            'urgences': queryset.filter(urgence=True).count(),
        }
        
        stats['par_type'] = {}
        for type_value, type_label in TypeConsultation.choices:
            stats['par_type'][type_label] = queryset.filter(type_consultation=type_value).count()
        
        stats['par_medecin'] = {}
        medecins = queryset.values('medecin__username').annotate(count=Count('id'))
        for medecin in medecins:
            if medecin['medecin__username']:
                stats['par_medecin'][medecin['medecin__username']] = medecin['count']
        
        return Response(stats)


class AntecedentMedicalViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des antécédents médicaux"""
    queryset = AntecedentMedical.objects.all()
    serializer_class = AntecedentMedicalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AntecedentMedical.objects.all()
        
        detenu_id = self.request.query_params.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        return queryset.order_by('-created_at')


class VaccinationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des vaccinations"""
    queryset = Vaccination.objects.all()
    serializer_class = VaccinationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Vaccination.objects.all()
        
        detenu_id = self.request.query_params.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        return queryset.order_by('-date_vaccination')
    
    def perform_create(self, serializer):
        serializer.save(medecin_vaccinateur=self.request.user)