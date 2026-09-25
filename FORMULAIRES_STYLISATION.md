# 📋 Guide de Stylisation des Formulaires

## ✅ Formulaires stylisés

1. **Administrateur de prison** (`admin_prison_form.html`) ✅
2. **Centre pénitentiaire** (`centre_form.html`) ✅
3. **Personnel** (`personnel_form.html`) ✅
4. **Visiteur** (`visiteur_form.html`) ✅
5. **Visite** (`visite_form.html`) ✅
6. **Détenu** (`form_compact.html`) - En cours ⚠️

## 🎨 Style appliqué

Tous les formulaires utilisent maintenant :
- **Fichier CSS partagé** : `static/css/form_styles.css`
- **Design compact** : Espacements optimisés, grille responsive
- **Style professionnel** : Dégradés, ombres, animations
- **Validation en temps réel** : Feedback visuel immédiat
- **Placeholders informatifs** : Aide contextuelle pour chaque champ

## 📝 Modifications apportées

### CSS Partagé
- ✅ Création de `static/css/form_styles.css` avec tous les styles communs
- ✅ Variables CSS pour les couleurs et dégradés
- ✅ Animations et transitions
- ✅ Design responsive

### Formulaires Python
- ✅ Placeholders ajoutés dans `CentreForm`
- ✅ Placeholders ajoutés dans `AdminPrisonForm`
- ✅ Placeholders ajoutés dans `VisiteurForm`
- ✅ Placeholders ajoutés dans `VisiteForm`
- ✅ Placeholders ajoutés dans `PersonnelForm`

### Templates HTML
- ✅ Structure HTML compacte et organisée
- ✅ Sections avec titres stylisés
- ✅ Grille responsive (3 colonnes → 1 colonne sur mobile)
- ✅ Boutons avec icônes et effets hover
- ✅ Messages d'erreur contextuels

## 📝 Formulaires à styliser

### Priorité haute
1. **Détenu** (`form_compact.html`, `form.html`)
2. **Visite** (`visite_form.html`)
3. **Visiteur** (`visiteur_form.html`)

### Priorité moyenne
4. **Consultation médicale** (si existe)
5. **Transfert/Libération** (si existe)

## 🔧 Instructions pour styliser un formulaire

### 1. Ajouter le CSS partagé
```html
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/form_styles.css' %}">
{% endblock %}
```

### 2. Structure HTML de base
```html
<div class="form-container">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="form-title"><i class="bi bi-icon"></i> {{ title }}</h1>
        <a href="{% url 'liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour
        </a>
    </div>

    <div class="form-card">
        <form method="post" novalidate>
            {% csrf_token %}
            
            <!-- Section -->
            <div class="form-section">
                <div class="section-title">
                    <i class="bi bi-icon"></i> Titre Section
                </div>
                <div class="form-grid">
                    <div class="form-group">
                        <label for="{{ form.champ.id_for_label }}" class="form-label">Label *</label>
                        {{ form.champ }}
                        {% if form.champ.errors %}
                        <div class="invalid-feedback">{{ form.champ.errors.0 }}</div>
                        {% endif %}
                        <small class="help-text">Aide contextuelle</small>
                    </div>
                </div>
            </div>

            <!-- Actions -->
            <div class="action-buttons">
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-circle"></i> {{ action }}
                </button>
                <a href="{% url 'liste' %}" class="btn btn-secondary">
                    <i class="bi bi-x-circle"></i> Annuler
                </a>
            </div>
        </form>
    </div>
</div>
```

### 3. Ajouter des placeholders dans le formulaire Python
```python
widgets = {
    'champ': forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Exemple de placeholder',
        'required': True
    }),
}
```

### 4. JavaScript de validation (optionnel)
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    // Validation en temps réel
});
```

## 📦 Fichier CSS partagé

Le fichier `static/css/form_styles.css` contient tous les styles communs :
- Variables CSS pour les couleurs et dégradés
- Styles pour les sections, labels, inputs
- Animations et transitions
- Responsive design

## 🎯 Caractéristiques du style

- **Compact** : Espacements réduits, design dense
- **Professionnel** : Dégradés, ombres, effets hover
- **Responsive** : Adaptation mobile automatique
- **Accessible** : Labels clairs, feedback visuel
- **Moderne** : Animations subtiles, transitions fluides
