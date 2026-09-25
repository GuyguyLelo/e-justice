# e-Detenu - Système de Gestion des Centres Pénitentiaires

## 🏛️ Description

e-Detenu est une application web Django complète pour la gestion des centres pénitentiaires en République Démocratique du Congo (RDC). Cette solution offre une architecture modulaire et sécurisée avec une API REST complète.

## 🚀 Fonctionnalités

### 👥 Gestion des Utilisateurs
- **Rôles personnalisés** : Admin, Directeur, Agent, Médecin, Visiteur
- **Authentification JWT** sécurisée
- **Permissions granulaires** selon les rôles

### 🏢 Gestion des Détenus
- **Fiches complètes** des détenus
- **Historique des modifications**
- **Suivi des libérations et transferts**
- **Statistiques détaillées**

### 👨‍💼 Gestion du Personnel
- **Profils professionnels** complets
- **Formations et sanctions**
- **Suivi des carrières**

### 👥 Gestion des Visites
- **Planification des visites**
- **Contrôle des objets**
- **Suivi des visiteurs**

### 🏥 Soins Médicaux
- **Dossiers médicaux** complets
- **Consultations et prescriptions**
- **Antécédents et vaccinations**
- **Gestion des médicaments**

### 📦 Logistique
- **Gestion des stocks**
- **Commandes et fournisseurs**
- **Mouvements de stock**

### 📊 Rapports et Statistiques
- **Rapports personnalisables**
- **Tableaux de bord**
- **Statistiques en temps réel**

## 🛠️ Technologies

- **Backend** : Django 4.2.7, Django REST Framework
- **Base de données** : PostgreSQL
- **Authentification** : JWT (Simple JWT)
- **Documentation** : Swagger/OpenAPI
- **Sécurité** : CORS, Permissions DRF

## 📋 Prérequis

- Python 3.8+
- PostgreSQL 12+
- pip

## 🚀 Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd e-Detenu
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de l'environnement
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer le fichier .env avec vos paramètres
# - SECRET_KEY
# - Configuration de la base de données PostgreSQL
# - Autres paramètres selon vos besoins
```

### 5. Configuration de la base de données
```bash
# Créer la base de données PostgreSQL
createdb edetenu

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur et des données de démonstration
python scripts/init_data.py
```

### 6. Lancer le serveur
```bash
python manage.py runserver
```

## 📚 API Documentation

Une fois le serveur lancé, accédez à la documentation interactive :

- **Swagger UI** : http://localhost:8000/api/docs/
- **ReDoc** : http://localhost:8000/api/redoc/
- **Schema OpenAPI** : http://localhost:8000/api/schema/

## 🔐 Authentification

### Obtenir un token JWT
```bash
curl -X POST http://localhost:8000/api/auth/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Utiliser le token
```bash
curl -X GET http://localhost:8000/api/detenus/detenus/ \
  -H "Authorization: Bearer <your-token>"
```

## 👥 Comptes par défaut

Après l'initialisation, les comptes suivants sont créés :

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| admin | admin123 | Administrateur |
| directeur | directeur123 | Directeur |
| agent1 | agent123 | Agent |
| medecin1 | medecin123 | Médecin |

## 🏗️ Architecture

```
e-Detenu/
├── apps/                    # Applications Django
│   ├── comptes/            # Gestion des utilisateurs
│   ├── detenus/            # Gestion des détenus
│   ├── personnel/          # Gestion du personnel
│   ├── visites/            # Gestion des visites
│   ├── soins/              # Soins médicaux
│   ├── logistique/         # Gestion logistique
│   └── rapports/           # Rapports et statistiques
├── scripts/                # Scripts utilitaires
├── static/                 # Fichiers statiques
├── media/                  # Fichiers uploadés
└── requirements.txt        # Dépendances Python
```

## 🔒 Sécurité

- **Authentification JWT** avec rotation des tokens
- **Permissions granulaires** par rôle
- **Validation des données** stricte
- **CORS configuré** pour les environnements de production
- **Logs de sécurité** complets

## 📊 Fonctionnalités Avancées

### Statistiques en Temps Réel
- Nombre total de détenus
- Répartition par statut
- Statistiques par âge et sexe
- Suivi des visites et consultations

### Rapports Personnalisables
- Génération de rapports PDF
- Tableaux de bord interactifs
- Export de données
- Planification automatique

### Gestion des Stocks
- Alertes de stock faible
- Suivi des expirations
- Mouvements de stock
- Commandes automatisées

## 🚀 Déploiement

### Production
1. Configurer les variables d'environnement
2. Utiliser une base de données PostgreSQL en production
3. Configurer un serveur web (Nginx + Gunicorn)
4. Activer HTTPS
5. Configurer les logs et monitoring

### Docker (Optionnel)
```bash
# Créer un Dockerfile
# Configurer docker-compose.yml
# Lancer avec Docker
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou support :
- Email : support@edetenu.rdc
- Documentation : http://localhost:8000/api/docs/

## 🎯 Roadmap

- [ ] Interface web React/Vue.js
- [ ] Notifications push
- [ ] Intégration SMS/Email
- [ ] Module de comptabilité
- [ ] Application mobile
- [ ] Intégration biométrique

---

**e-Detenu** - Système de gestion moderne pour les centres pénitentiaires en RDC 🇨🇩