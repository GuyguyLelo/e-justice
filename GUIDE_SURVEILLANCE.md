# 📋 Guide Simple du Système de Surveillance e-Detenu

## 🎯 **À Quoi Ça Sert ?**

Le système de surveillance permet de **reconnaître les détenus automatiquement** grâce aux caméras de surveillance installées dans les centres pénitenciers.

---

## 🏗️ **Comment Ça Marche ?**

### 1. **Les Caméras**
- 📹 Des caméras sont installées dans les zones stratégiques (couloirs, entrées, cours...)
- Elles filment en continu et envoient les images au système

### 2. **La Reconnaissance Faciale**
- 👁️ Le système analyse les images des caméras en temps réel
- 🔍 Il détecte les visages dans les vidéos
- 🧠 Il compare chaque visage détecté avec la base de données des détenus

### 3. **Les Profils Faciaux**
- 📸 Chaque détenu a une photo de référence enregistrée
- 💾 Le système crée une "empreinte numérique" de chaque visage
- 🔐 Cette empreinte permet d'identifier rapidement les détenus

---

## 🚨 **Les Alertes Automatiques**

Le système génère des alertes quand :

1. **Visage Inconnu Détecté**
   - Une personne non identifiée est vue par une caméra
   - ⚠️ Alerte : "Visage inconnu dans la zone X"

2. **Détenu dans Zone Interdite**
   - Un détenu est détecté dans une zone où il ne devrait pas être
   - ⚠️ Alerte : "Détenu Jean Dupont dans zone interdite"

3. **Caméra Hors Service**
   - Une caméra ne fonctionne plus
   - ⚠️ Alerte : "Caméra entrée principale hors service"

---

## 📊 **Le Dashboard de Surveillance**

Quand vous cliquez sur "Surveillance", vous voyez :

### 📈 **Statistiques en Temps Réel**
- **Caméras** : Combien sont actives/inactives
- **Détections** : Nombre de visages reconnus aujourd'hui
- **Alertes** : Alertes en cours et leur niveau de gravité

### 🎛️ **Actions Possibles**
- **Voir les caméras** : Liste de toutes les caméras avec leur statut
- **Consulter les détections** : Historique de toutes les reconnaissances
- **Gérer les alertes** : Voir et traiter les alertes actives
- **Gérer les profils** : Ajouter/modifier les photos des détenus

---

## 🔧 **Comment Utiliser le Système**

### Étape 1 : **Configuration des Caméras**
1. Allez dans "Caméras"
2. Ajoutez chaque caméra avec :
   - Nom (ex: "Caméra Entrée Principale")
   - Emplacement (ex: "Portail d'entrée")
   - Adresse IP pour se connecter

### Étape 2 : **Création des Profils Faciaux**
1. Allez dans "Profils Faciaux"
2. Pour chaque détenu :
   - Ajoutez une photo claire du visage
   - Le système crée automatiquement l'empreinte faciale

### Étape 3 : **Démarrage de la Surveillance**
1. Dans le dashboard, cliquez "Initialiser le Système"
2. Pour chaque caméra, cliquez "Démarrer la détection"
3. Le système commence à analyser en temps réel

---

## 📱 **Exemple Concret**

### Scénario Normal :
1. **10h15** - Le détenu **Jean Dupont** passe dans le couloir
2. **Camera A** le filme et envoie l'image
3. **Système** détecte son visage et le reconnaît
4. **Résultat** : Détection enregistrée, aucune alerte

### Scénario d'Alerte :
1. **14h30** - Une personne inconnue entre dans la cour
2. **Camera B** la filme
3. **Système** détecte un visage mais ne le trouve dans aucune base
4. **Alerte** générée : "Visage inconnu détecté dans la cour"
5. **Agent** reçoit l'alerte et peut intervenir

---

## 🎯 **Les Avantages**

### ✅ **Pour la Sécurité**
- **Surveillance 24/7** sans fatigue humaine
- **Réactivité immédiate** aux intrusions
- **Historique complet** de tous les mouvements

### ✅ **Pour la Gestion**
- **Preuves vidéo** automatiques
- **Statistiques précises** des déplacements
- **Alertes ciblées** selon les zones

### ✅ **Pour le Personnel**
- **Gain de temps** : moins de rondes manuelles
- **Concentration** sur les tâches importantes
- **Sécurité** renforcée pour tous

---

## 🚀 **Pour Commencer**

1. **Connectez-vous** avec `admin` / `admin123`
2. **Cliquez sur "Surveillance"** dans le menu
3. **Explorez le dashboard** pour voir les statistiques
4. **Commencez par ajouter une caméra** dans "Caméras"
5. **Ajoutez des profils faciaux** pour quelques détenus

---

## 💡 **Conseils d'Utilisation**

- 📸 **Photos de bonne qualité** : Visages bien éclairés, de face
- 🎯 **Caméras bien positionnées** : Zones de passage obligatoires
- 🔧 **Testez régulièrement** : Vérifiez que les caméras fonctionnent
- 📊 **Consultez les alertes** : Traitez-les rapidement

---

## ❓ **Questions Fréquentes**

**Q : Est-ce que ça fonctionne avec n'importe quelle caméra ?**
R : Oui, avec les caméras IP compatibles RTSP.

**Q : Que faire si le système fait une erreur ?**
R : Vous pouvez marquer les alertes comme "Fausses alertes" et corriger les profils.

**Q : Les données sont-elles sécurisées ?**
R : Oui, tout est crypté et uniquement accessible par le personnel autorisé.

---

**Le système est conçu pour être un assistant intelligent qui aide le personnel à maintenir la sécurité de manière plus efficace et plus sûre !** 🛡️
