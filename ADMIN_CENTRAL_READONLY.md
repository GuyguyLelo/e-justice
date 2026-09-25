# Admin Central - Accès en Lecture Seule

## 🎯 Objectif
L'admin central peut voir toutes les données de tous les centres mais ne peut pas les modifier (créer, éditer, supprimer).

## ✅ Modifications Appliquées

### **1. Permissions Ajoutées (apps/comptes/models.py)**

#### **Nouvelles Méthodes**
```python
def can_view_all_data(self):
    """Vérifie si l'utilisateur peut voir toutes les données (admin central en lecture seule)"""
    return self.role == Role.ADMIN_CENTRAL

def can_edit_detenus(self):
    """Vérifie si l'utilisateur peut modifier les détenus"""
    # Admin central ne peut PAS modifier les détenus (lecture seule)
    # Admins de centre peuvent modifier les détenus de leur centre
    return (self.role in [Role.ADMIN, Role.DIRECTEUR, Role.AGENT] and 
            hasattr(self, 'adminprison'))

def can_edit_personnel(self):
    """Vérifie si l'utilisateur peut modifier le personnel"""
    # Admin central ne peut PAS modifier le personnel (lecture seule)
    # Admins de centre peuvent modifier le personnel de leur centre
    return (self.role in [Role.ADMIN, Role.DIRECTEUR] and 
            hasattr(self, 'adminprison'))

def can_edit_visites(self):
    """Vérifie si l'utilisateur peut modifier les visites"""
    # Admin central ne peut PAS modifier les visites (lecture seule)
    # Admins de centre peuvent modifier les visites de leur centre
    return (self.role in [Role.ADMIN, Role.DIRECTEUR, Role.AGENT] and 
            hasattr(self, 'adminprison'))
```

### **2. Vues Modifiées**

#### **Détenus (apps/detenus/views_web.py)**
- **`detenu_create_view`**: Vérification `user.can_edit_detenus()`
- **`detenu_edit_view`**: Vérification `user.can_edit_detenus()`
- **`detenu_delete_view`**: Vérification `user.can_edit_detenus()`
- **`detenus_list_view`**: Admin central voit tous les détenus

#### **Personnel (apps/personnel/views_web.py)**
- **`personnel_create_view`**: Vérification `user.can_edit_personnel()`
- **`personnel_edit_view`**: Vérification `user.can_edit_personnel()`
- **`personnel_delete_view`**: Vérification `user.can_edit_personnel()`
- **`personnel_list_view`**: Admin central voit tout le personnel

#### **Visites (apps/visites/views_web.py)**
- **`visite_create_view`**: Vérification `user.can_edit_visites()`
- **`visite_edit_view`**: Vérification `user.can_edit_visites()`
- **`visite_delete_view`**: Vérification `user.can_edit_visites()`
- **`visites_list_view`**: Admin central voit toutes les visites

### **3. Context Variables Ajoutées**

#### **Templates Context**
```python
'can_edit': user.can_edit_detenus(),      # Pour détenus
'can_edit': user.can_edit_personnel(),    # Pour personnel  
'can_edit': user.can_edit_visites(),      # Pour visites
```

## 🔐 Comportement par Rôle

### **Admin Central (admin_central)**
- ✅ **Voir**: Toutes les données de tous les centres
- ❌ **Créer**: Détenu, personnel, visite → Message d'erreur
- ❌ **Modifier**: Détenu, personnel, visite → Message d'erreur
- ❌ **Supprimer**: Détenu, personnel, visite → Message d'erreur

### **Admin Centre (admin_centre_test)**
- ✅ **Voir**: Données de son centre uniquement
- ✅ **Créer**: Détenu, personnel, visite pour son centre
- ✅ **Modifier**: Détenu, personnel, visite de son centre
- ✅ **Supprimer**: Détenu, personnel, visite de son centre

## 📝 Messages d'Erreur

#### **Admin Central**
- "Vous n'avez pas la permission de créer des détenus."
- "Vous n'avez pas la permission de modifier les détenus."
- "Vous n'avez pas la permission de supprimer les détenus."
- "Vous n'avez pas la permission de créer du personnel."
- "Vous n'avez pas la permission de modifier le personnel."
- "Vous n'avez pas la permission de supprimer du personnel."
- "Vous n'avez pas la permission de créer des visites."
- "Vous n'avez pas la permission de modifier les visites."
- "Vous n'avez pas la permission de supprimer des visites."

## 🎨 Templates à Modifier

Pour une meilleure UX, les templates devraient utiliser la variable `can_edit` pour cacher les boutons:

```html
{% if can_edit %}
<button class="btn btn-primary">Modifier</button>
<button class="btn btn-danger">Supprimer</button>
{% endif %}
```

## 🚀 Tests Recommandés

### **Test 1: Admin Central**
1. Se connecter avec `admin_central` / `admin123`
2. Accéder aux listes: détenus, personnel, visites
3. **Vérifier**: Toutes les données visibles
4. **Tenter**: Créer → Message d'erreur
5. **Tenter**: Modifier → Message d'erreur
6. **Tenter**: Supprimer → Message d'erreur

### **Test 2: Admin Centre**
1. Se connecter avec `admin_centre_test` / `admin123`
2. Accéder aux listes: détenus, personnel, visites
3. **Vérifier**: Données de son centre uniquement
4. **Tenter**: Créer → ✅ Fonctionne
5. **Tenter**: Modifier → ✅ Fonctionne
6. **Tenter**: Supprimer → ✅ Fonctionne

## 🎯 Résultat

L'admin central a maintenant un accès **lecture seule** complète sur toutes les données du système, tandis que les admins de centre gardent leurs pleines permissions sur leur centre respectif !
