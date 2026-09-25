# 📋 Documentation des Formulaires e-Detenu

## 🎯 Vue d'ensemble

Les formulaires Django ont été créés pour chaque module de l'application e-Detenu, offrant une interface utilisateur cohérente et des validations robustes.

## 📱 Modules et Formulaires

### 👥 Comptes (`apps.comptes.forms`)

#### Formulaires principaux
- **`UtilisateurCreationForm`** : Création d'utilisateurs avec rôles
- **`UtilisateurChangeForm`** : Modification des utilisateurs
- **`ChangePasswordForm`** : Changement de mot de passe

#### Fonctionnalités
- Validation des rôles (Admin, Directeur, Agent, Médecin, Visiteur)
- Validation des mots de passe
- Gestion des permissions

### 🏢 Détenus (`apps.detenus.forms`)

#### Formulaires principaux
- **`DetenuForm`** : Gestion complète des détenus
- **`LiberationForm`** : Libération d'un détenu
- **`TransfertForm`** : Transfert d'un détenu
- **`RechercheDetenuForm`** : Recherche et filtrage

#### Fonctionnalités
- Validation des matricules uniques
- Validation des dates (libération > incarcération)
- Recherche multicritères

### 👨‍💼 Personnel (`apps.personnel.forms`)

#### Formulaires principaux
- **`PersonnelForm`** : Gestion du personnel
- **`FormationPersonnelForm`** : Formations du personnel
- **`SanctionPersonnelForm`** : Sanctions du personnel
- **`UtilisateurPersonnelForm`** : Création utilisateur + personnel

#### Fonctionnalités
- Validation des matricules
- Gestion des formations et sanctions
- Création automatique d'utilisateurs

### 👥 Visites (`apps.visites.forms`)

#### Formulaires principaux
- **`VisiteurForm`** : Gestion des visiteurs
- **`VisiteForm`** : Gestion des visites
- **`ObjetVisiteForm`** : Objets apportés
- **`PlanificationVisiteForm`** : Planification
- **`ControleVisiteForm`** : Contrôle des visites

#### Fonctionnalités
- Validation des dates de visite
- Contrôle des objets
- Gestion des statuts

### 🏥 Soins (`apps.soins.forms`)

#### Formulaires principaux
- **`ConsultationForm`** : Consultations médicales
- **`MedicamentForm`** : Gestion des médicaments
- **`PrescriptionForm`** : Prescriptions
- **`AntecedentMedicalForm`** : Antécédents médicaux
- **`VaccinationForm`** : Vaccinations

#### Fonctionnalités
- Validation des stocks de médicaments
- Gestion des prescriptions
- Suivi médical complet

### 📦 Logistique (`apps.logistique.forms`)

#### Formulaires principaux
- **`FournisseurForm`** : Gestion des fournisseurs
- **`ProduitForm`** : Gestion des produits
- **`CommandeForm`** : Commandes
- **`LigneCommandeForm`** : Lignes de commande
- **`MouvementStockForm`** : Mouvements de stock

#### Fonctionnalités
- Validation des stocks
- Gestion des commandes
- Suivi des mouvements

### 📊 Rapports (`apps.rapports.forms`)

#### Formulaires principaux
- **`RapportForm`** : Création de rapports
- **`ModeleRapportForm`** : Modèles de rapports
- **`TableauBordForm`** : Tableaux de bord
- **`GenerationRapportForm`** : Génération de rapports
- **`FiltreRapportForm`** : Filtres avancés

#### Fonctionnalités
- Génération de rapports personnalisés
- Filtres multicritères
- Tableaux de bord interactifs

## 🎨 Classes CSS Utilisées

Tous les formulaires utilisent les classes Bootstrap pour un style cohérent :

```html
<!-- Champs de saisie -->
<input class="form-control" />

<!-- Sélecteurs -->
<select class="form-control" />

<!-- Zones de texte -->
<textarea class="form-control" rows="3" />

<!-- Cases à cocher -->
<input class="form-check-input" type="checkbox" />

<!-- Dates -->
<input class="form-control" type="date" />
```

## 🔧 Utilisation

### Exemple d'utilisation basique

```python
from apps.detenus.forms import DetenuForm

# Création d'un formulaire
form = DetenuForm()

# Avec des données
form = DetenuForm(data=request.POST)

# Validation
if form.is_valid():
    detenu = form.save()
```

### Utilisation avec le gestionnaire central

```python
from forms_manager import formulaires

# Obtenir un formulaire
form = formulaires.get_form('detenu')

# Obtenir tous les formulaires d'un module
forms = formulaires.get_all_forms()['detenus']
```

## ✅ Validations Implémentées

### Validations communes
- **Unicité** : Matricules, emails, usernames
- **Dates** : Cohérence des dates (début < fin)
- **Quantités** : Valeurs positives
- **Stocks** : Cohérence des niveaux de stock

### Validations spécifiques
- **Détenus** : Matricules uniques, dates d'incarcération
- **Personnel** : Dates d'embauche, niveaux de salaire
- **Visites** : Durées de visite (15-180 min)
- **Médicaments** : Dates d'expiration, stocks minimums
- **Commandes** : Quantités commandées vs livrées

## 🎯 Bonnes Pratiques

### 1. Validation côté client et serveur
```python
# Validation dans le formulaire
def clean_matricule(self):
    matricule = self.cleaned_data.get('matricule')
    if Detenu.objects.filter(matricule=matricule).exists():
        raise ValidationError("Ce matricule existe déjà.")
    return matricule
```

### 2. Messages d'erreur personnalisés
```python
# Dans le template
{% if form.errors %}
    <div class="alert alert-danger">
        {% for field, errors in form.errors.items %}
            {% for error in errors %}
                <p>{{ error }}</p>
            {% endfor %}
        {% endfor %}
    </div>
{% endif %}
```

### 3. Filtrage des choix
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Filtrer les détenus incarcérés
    self.fields['detenu'].queryset = Detenu.objects.filter(statut='INCARCERE')
```

## 🚀 Intégration Frontend

### Avec Bootstrap
```html
<div class="form-group">
    <label for="{{ form.nom.id_for_label }}">{{ form.nom.label }}</label>
    {{ form.nom }}
    {% if form.nom.errors %}
        <div class="invalid-feedback">
            {{ form.nom.errors.0 }}
        </div>
    {% endif %}
</div>
```

### Avec JavaScript
```javascript
// Validation en temps réel
document.getElementById('id_matricule').addEventListener('blur', function() {
    // Vérifier l'unicité du matricule
    fetch('/api/check-matricule/', {
        method: 'POST',
        body: JSON.stringify({matricule: this.value})
    })
    .then(response => response.json())
    .then(data => {
        if (!data.available) {
            this.classList.add('is-invalid');
        }
    });
});
```

## 📝 Exemples d'Utilisation

### Création d'un détenu
```python
from apps.detenus.forms import DetenuForm

form = DetenuForm(data={
    'matricule': 'DET001',
    'nom': 'Mukamba',
    'prenom': 'Jean',
    'sexe': 'M',
    'date_naissance': '1990-01-01',
    'date_incarceration': '2024-01-01',
    'motif_incarceration': 'Vol à main armée',
    'cellule': 'A1',
    'regime': 'PREVENTIF'
})

if form.is_valid():
    detenu = form.save()
    print(f"Détenu créé : {detenu.nom_complet}")
```

### Recherche de détenus
```python
from apps.detenus.forms import RechercheDetenuForm

form = RechercheDetenuForm(data={
    'search': 'Mukamba',
    'statut': 'INCARCERE',
    'regime': 'PREVENTIF'
})

if form.is_valid():
    # Appliquer les filtres
    detenus = Detenu.objects.all()
    if form.cleaned_data['search']:
        detenus = detenus.filter(nom__icontains=form.cleaned_data['search'])
    # ... autres filtres
```

## 🔍 Débogage

### Vérifier les erreurs de formulaire
```python
if not form.is_valid():
    print("Erreurs de validation :")
    for field, errors in form.errors.items():
        print(f"{field}: {errors}")
```

### Tester les validations
```python
# Test d'unicité
form1 = DetenuForm(data={'matricule': 'DET001', 'nom': 'Test'})
form1.save()

form2 = DetenuForm(data={'matricule': 'DET001', 'nom': 'Test2'})
assert not form2.is_valid()  # Doit échouer
```

---

**Les formulaires e-Detenu offrent une interface complète et sécurisée pour la gestion des centres pénitentiaires ! 🎉**






