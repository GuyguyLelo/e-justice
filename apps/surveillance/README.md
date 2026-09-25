# Module de Surveillance et Reconnaissance Faciale pour e-Detenu

## 📋 Vue d'ensemble

Ce module ajoute des fonctionnalités de surveillance avancées au système e-Detenu, permettant la reconnaissance faciale des détenus à partir des caméras de surveillance des centres pénitenciers.

## 🚀 Fonctionnalités

### 📹 Gestion des Caméras
- **Configuration multi-types**: Intérieure, extérieure, PTZ, dôme, etc.
- **Gestion des flux vidéo**: Support RTSP et autres protocoles
- **Contrôle de statut**: Active, inactive, maintenance, hors service
- **Zones de surveillance**: Définition de zones spécifiques avec seuils d'alerte

### 👁️ Reconnaissance Faciale
- **Détection en temps réel**: Analyse des flux vidéo continue
- **Identification des détenus**: Comparaison avec la base de données des profils
- **Gestion des profils faciaux**: Encodage et stockage des visages
- **Seuils de confiance**: Configuration de la sensibilité de détection

### 🚨 Système d'Alertes
- **Alertes automatiques**: Détection de visages inconnus ou zones interdites
- **Niveaux de criticité**: Information, Attention, Warning, Critique
- **Gestion du cycle de vie**: Ouverture, assignation, résolution
- **Notifications en temps réel**: Interface de monitoring des alertes actives

### 📊 Dashboard et Monitoring
- **Statistiques en temps réel**: Caméras actives, détections, alertes
- **Graphiques analytiques**: Visualisation des tendances
- **Historique complet**: Traçabilité de tous les événements
- **Interface responsive**: Compatible desktop et mobile

## 🛠️ Installation

### 1. Dépendances

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Dépendances système pour OpenCV (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3-opencv libopencv-dev dlib-python
```

### 2. Configuration

```bash
# Appliquer les migrations
python manage.py migrate surveillance

# Créer un superutilisateur si nécessaire
python manage.py createsuperuser
```

### 3. Démarrage

```bash
# Démarrer le serveur
python manage.py runserver

# Accéder au module de surveillance
# http://localhost:8000/surveillance/
```

## 📖 Utilisation

### Configuration des Caméras

1. **Ajouter une caméra**:
   - Accéder à `/surveillance/cameras/`
   - Cliquer sur "Ajouter une caméra"
   - Configurer l'adresse IP, port, et emplacement

2. **Définir les zones**:
   - Accéder au détail d'une caméra
   - Ajouter des zones de surveillance
   - Configurer les seuils d'alerte

### Gestion des Profils Faciaux

1. **Créer un profil**:
   - Sélectionner un détenu existant
   - Uploader une photo de référence
   - Le système génère automatiquement l'encodage facial

2. **Activer la reconnaissance**:
   - Initialiser le système depuis le dashboard
   - Démarrer la détection sur les caméras souhaitées

### Monitoring des Alertes

1. **Consultation en temps réel**:
   - Dashboard principal pour les alertes actives
   - Filtres par niveau, type, et statut

2. **Traitement des alertes**:
   - Assigner à un utilisateur
   - Ajouter des notes de résolution
   - Marquer comme résolue ou fausse alerte

## 🔧 API REST

### Endpoints principaux

```bash
# Caméras
GET    /api/surveillance/cameras/
POST   /api/surveillance/cameras/
GET    /api/surveillance/cameras/{id}/
PUT    /api/surveillance/cameras/{id}/
DELETE /api/surveillance/cameras/{id}/

# Détections
GET    /api/surveillance/detections/
POST   /api/surveillance/detections/
GET    /api/surveillance/detections/{id}/
POST   /api/surveillance/detections/{id}/traiter/

# Alertes
GET    /api/surveillance/alertes/
POST   /api/surveillance/alertes/
GET    /api/surveillance/alertes/{id}/
POST   /api/surveillance/alertes/{id}/assigner/
POST   /api/surveillance/alertes/{id}/resoudre/

# Dashboard
GET    /api/surveillance/dashboard/dashboard/
POST   /api/surveillance/dashboard/initialiser-systeme/
```

## 🏗️ Architecture

### Modèles de données

- **Camera**: Informations des caméras de surveillance
- **ZoneSurveillance**: Zones de détection spécifiques
- **ProfilFacialDetenu**: Profils faciaux des détenus
- **DetectionFaciale**: Enregistrements des détections
- **AlerteSurveillance**: Gestion des alertes
- **HistoriqueSurveillance**: Journal des événements

### Services

- **FaceRecognitionService**: Traitement de la reconnaissance faciale
- **VideoStreamService**: Gestion des flux vidéo
- **DetectionService**: Orchestration de la détection
- **AlertService**: Gestion des alertes

## 🔒 Sécurité

- **Permissions granulaires**: Rôles et accès contrôlés
- **Journalisation complète**: Traçabilité de toutes les actions
- **Validation des données**: Protection contre les injections
- **Chiffrement**: Sécurisation des données sensibles

## 📈 Performance

- **Traitement asynchrone**: Non-bloquant pour les flux vidéo
- **Optimisation des requêtes**: Sélections et indexations
- **Cache intelligent**: Mise en cache des profils faciaux
- **Monitoring ressources**: Surveillance CPU et mémoire

## 🐛 Dépannage

### Problèmes courants

1. **Import OpenCV manquant**:
   ```bash
   pip install opencv-python
   ```

2. **Caméra hors ligne**:
   - Vérifier la connectivité réseau
   - Confirmer l'URL du flux RTSP

3. **Reconnaissance faible**:
   - Ajuster le seuil de confiance
   - Améliorer la qualité des photos de référence

### Logs

```bash
# Logs Django
tail -f logs/django.log

# Logs spécifiques surveillance
grep "surveillance" logs/django.log
```

## 🔄 Mises à jour

Pour mettre à jour le module:

```bash
# Mettre à jour les dépendances
pip install -r requirements.txt

# Appliquer les nouvelles migrations
python manage.py migrate surveillance

# Redémarrer le serveur
python manage.py runserver
```

## 📞 Support

Pour toute question ou problème technique:

- Documentation API: `/api/docs/`
- Interface admin: `/admin/`
- Dashboard surveillance: `/surveillance/`

---

**Note**: Ce module nécessite des caméras IP compatibles et une infrastructure réseau adéquate pour un fonctionnement optimal.
