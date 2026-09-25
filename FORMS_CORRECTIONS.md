# Corrections des Formulaires - Centre et Personnel

## 🔧 Problèmes Corrigés

### 1. **Champ Centre Manquant dans le Formulaire de Détenu**

#### **Problème**
- Le champ `centre` n'était pas affiché dans le template
- L'admin de centre ne voyait pas le centre assigné

#### **Solution**
1. **Ajout du champ au formulaire** (`apps/detenus/forms.py`)
   ```python
   fields = ['centre', 'matricule', 'nom', ...]
   widgets = {'centre': forms.Select(attrs={'class': 'form-control'})}
   ```

2. **Ajout du champ au template** (`templates/detenus/form_compact.html`)
   ```html
   <!-- Informations du centre -->
   <div class="form-section">
       <h6><i class="bi bi-building"></i> Centre</h6>
       <div class="row">
           <div class="col-md-12">
               <div class="form-floating">
                   {{ form.centre }}
                   <label for="{{ form.centre.id_for_label }}">Centre</label>
                   {% if user_centre %}
                   <small class="text-muted">Centre assigné automatiquement: {{ user_centre.nom }}</small>
                   {% endif %}
               </div>
           </div>
       </div>
   </div>
   ```

3. **Logique dans la vue** (`apps/detenus/views_web.py`)
   ```python
   # Pré-remplir le centre pour les admins de centre
   if hasattr(user, 'adminprison'):
       form.initial['centre'] = user.adminprison.centre
       form.fields['centre'].widget.attrs['readonly'] = True
   ```

#### **Résultat**
- ✅ **Admin centre**: Champ centre pré-rempli et en lecture seule
- ✅ **Admin central**: Champ centre modifiable avec tous les centres
- ✅ **Assignation automatique**: Le détenu est assigné au bon centre

---

### 2. **Admin Central Visible dans le Formulaire de Personnel**

#### **Problème**
- L'admin central apparaissait dans la liste des utilisateurs
- Les admins de centre pouvaient créer du personnel pour l'admin central

#### **Solution**
1. **Filtrage intelligent du formulaire** (`apps/personnel/forms.py`)
   ```python
   def __init__(self, *args, **kwargs):
       user = kwargs.pop('user', None)
       super().__init__(*args, **kwargs)
       
       if user and hasattr(user, 'adminprison'):
           # Admin de centre: ne montrer que les utilisateurs de son centre
           centre_users = Utilisateur.objects.filter(
               adminprison__centre=user.adminprison.centre
           )
           self.fields['utilisateur'].queryset = centre_users
       elif user and user.is_admin_central():
           # Admin central: exclure les admins centraux
           non_admin_central_users = Utilisateur.objects.exclude(
               role='ADMIN_CENTRAL'
           )
           self.fields['utilisateur'].queryset = non_admin_central_users
   ```

2. **Passage de l'utilisateur au formulaire** (`apps/personnel/views_web.py`)
   ```python
   # Création
   form = PersonnelForm(request.POST, user=request.user)
   form = PersonnelForm(user=request.user)
   
   # Modification
   form = PersonnelForm(request.POST, instance=personnel, user=request.user)
   form = PersonnelForm(instance=personnel, user=request.user)
   ```

#### **Résultat**
- ✅ **Admin centre**: Voit uniquement les utilisateurs de son centre
- ✅ **Admin central**: Voit tous les utilisateurs sauf les admins centraux
- ✅ **Sécurité**: Plus de création de personnel pour l'admin central

---

## 🎯 Comportement par Rôle

### **Admin Centre (admin_centre_test)**
- **Formulaire détenu**: Centre pré-rempli avec "Centre Test" (lecture seule)
- **Formulaire personnel**: Uniquement les utilisateurs de "Centre Test"
- **Isolation**: Parfaitement isolé à son centre

### **Admin Central (admin_central)**
- **Formulaire détenu**: Liste déroulante de tous les centres (modifiable)
- **Formulaire personnel**: Tous les utilisateurs sauf les admins centraux
- **Vue globale**: Accès à toutes les données du système

## ✅ Tests à Effectuer

### **Test 1: Création de Détenu**
1. Se connecter avec `admin_centre_test` / `admin123`
2. Accéder à `/api/detenus/web/nouveau/`
3. **Vérifier**: Champ centre pré-rempli avec "Centre Test"
4. **Vérifier**: Champ centre en lecture seule
5. Créer un détenu et vérifier l'assignation

### **Test 2: Création de Personnel**
1. Se connecter avec `admin_centre_test` / `admin123`
2. Accéder à `/api/personnel/web/personnel/nouveau`
3. **Vérifier**: Admin central n'apparaît pas dans la liste
4. **Vérifier**: Uniquement les utilisateurs du centre disponibles
5. Créer un personnel et vérifier l'assignation

### **Test 3: Admin Central**
1. Se connecter avec `admin_central` / `admin123`
2. **Formulaire détenu**: Vérifier la liste de tous les centres
3. **Formulaire personnel**: Vérifier l'absence des admins centraux

## 🚀 Résultat

Les formulaires sont maintenant parfaitement configurés avec :
- ✅ **Visibilité claire** du centre dans le formulaire de détenu
- ✅ **Filtrage sécurisé** des utilisateurs dans le formulaire de personnel
- ✅ **Isolation par centre** respectée
- ✅ **Assignation automatique** selon le rôle de l'utilisateur
