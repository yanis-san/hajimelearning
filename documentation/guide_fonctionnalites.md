# Hajime Learning — Guide complet des fonctionnalités

> Dernière mise à jour : 22 février 2026

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Visiteur (non connecté)](#2-visiteur-non-connecté)
3. [Étudiant (utilisateur connecté)](#3-étudiant-utilisateur-connecté)
4. [Instructeur](#4-instructeur)
5. [Superuser / Staff](#5-superuser--staff)
6. [Système de brouillon (Draft)](#6-système-de-brouillon-draft)
7. [Système de paiement et accès](#7-système-de-paiement-et-accès)
8. [Notifications](#8-notifications)
9. [Support / Questions](#9-support--questions)
10. [SEO & Technique](#10-seo--technique)
11. [Stack technique](#11-stack-technique)

---

## 1. Vue d'ensemble

Hajime Learning est une plateforme LMS (Learning Management System) permettant à des instructeurs de créer et vendre des formations, et à des étudiants de les acheter et suivre leur progression.

### Les 3 rôles principaux

| Rôle | Qui ? | Accès |
|------|-------|-------|
| **Visiteur / Étudiant** | Tout le monde | Consulter, acheter, apprendre |
| **Instructeur** | Utilisateur avec un profil instructeur actif | Créer et gérer ses propres formations |
| **Superuser / Staff** | Administrateur | Tout gérer, approuver, modérer |

---

## 2. Visiteur (non connecté)

### Ce qu'il peut faire

| Action | URL | Description |
|--------|-----|-------------|
| **Page d'accueil** | `/` | Voir les formations mises en avant (`is_featured`) |
| **Catalogue** | `/catalogue/` | Parcourir toutes les formations publiées avec recherche et tri |
| **Détail d'un cours** | `/course/<slug>/` | Voir la page de vente (landing page) d'une formation |
| **Offres instructeur** | `/instructors/` | Voir les plans disponibles pour devenir instructeur |
| **Inscription** | `/accounts/signup/` | Créer un compte (email, nom, prénom, pays, etc.) |
| **Connexion** | `/accounts/login/` | Se connecter avec email + mot de passe |
| **Mot de passe oublié** | `/accounts/password/reset/` | Réinitialiser son mot de passe par email |

### Catalogue — Recherche et tri

- **Recherche** : par titre ou description courte (champ `q`)
- **Tri disponible** : titre (A→Z / Z→A), prix (croissant / décroissant), date (récent / ancien)
- Fonctionne en HTMX (rechargement partiel sans rafraîchir la page)

### Page de vente d'un cours

- Affiche les sections de la landing page (hero, texte, fonctionnalités, FAQ, témoignages, etc.)
- Programme de la formation (liste des modules et leçons publiés)
- Bouton d'achat / demande d'accès
- Bande-annonce vidéo si définie

---

## 3. Étudiant (utilisateur connecté)

### Profil

| Action | URL | Description |
|--------|-----|-------------|
| **Modifier son profil** | `/users/profile/` | Avatar, nom, téléphone, date de naissance, genre, pays, ville, adresse |

### Tableau de bord

| Action | URL | Description |
|--------|-----|-------------|
| **Mon tableau de bord** | `/dashboard/` | Liste des cours auxquels l'étudiant a accès (gratuits + achetés) |

### Suivre une formation

| Action | URL | Description |
|--------|-----|-------------|
| **Voir un cours acheté** | `/course/<slug>/` | Affiche la progression avec barre de pourcentage, liste des modules/leçons avec statut |
| **Voir une leçon** | `/course/<slug>/lesson/<slug>/` | Contenu de la leçon (texte markdown, vidéo Bunny, fichiers, quiz) |
| **Marquer une leçon terminée** | `/course/<slug>/lesson/<slug>/complete/` | Valide la progression — redirige vers la leçon suivante ou le cours si c'est la dernière |
| **Passer un quiz** | *(dans la leçon)* | Quiz interactif avec timer, 4 choix, correction et explication |

### Contenu d'une leçon

Les leçons sont composées de **blocs de contenu** (dans l'ordre) :

| Type de bloc | Description |
|--------------|-------------|
| **Texte** | Contenu Markdown rendu en HTML |
| **Vidéo** | Lecteur Bunny Stream (par ID vidéo) |
| **Audio** | Lecteur audio HTML5 avec fichier uploadé |
| **Fichier** | Téléchargement de document (PDF, etc.) + fichier de correction optionnel |
| **Quiz** | QCM interactif avec timer, score sauvegardé, explication par question |

### Leçons gratuites

- Certaines leçons sont marquées « Gratuit » → accessibles sans acheter le cours
- Sert d'aperçu / preview

### Acheter une formation

Voir [section 7 — Système de paiement](#7-système-de-paiement-et-accès).

### Support

Voir [section 9 — Support / Questions](#9-support--questions).

### Notifications

Voir [section 8 — Notifications](#8-notifications).

---

## 4. Instructeur

### Devenir instructeur

1. Aller sur `/instructors/` pour voir les offres
2. Choisir un plan → `/instructors/request/<slug>/`
3. Uploader une preuve de paiement
4. Attendre l'approbation → page d'attente `/instructors/pending/`
5. Une fois approuvé par l'admin → profil instructeur créé automatiquement (signal)

### Plans instructeur

Chaque plan définit :
- Nombre maximum de formations
- Nombre maximum de modules par formation
- Nombre maximum de leçons par formation
- Pourcentage de revenus
- Prix du plan
- Liste de fonctionnalités affichées

### Upgrade de plan

- Un instructeur existant peut changer d'offre depuis `/instructors/`
- Le dashboard affiche un lien "Changer d'offre →"
- Les cartes montrent : "Offre actuelle", "Offre inférieure", ou "Passer à X"
- Soumission d'une nouvelle demande avec preuve de paiement

### Tableau de bord instructeur

| Action | URL | Description |
|--------|-----|-------------|
| **Dashboard** | `/instructors/dashboard/` | Liste de ses formations avec stats (modules, leçons, étudiants inscrits), compteurs totaux |

### Créer / Éditer une formation

| Action | URL | Description |
|--------|-----|-------------|
| **Créer un cours** | `/instructors/courses/create/` | Formulaire : titre, slug (auto-généré), descriptions, prix, thumbnail, vidéo trailer, SEO, publié/brouillon |
| **Éditer un cours** | `/instructors/courses/<slug>/edit/` | Modifier les champs d'un cours existant |

**Champs disponibles pour l'instructeur** (pas `is_featured` ni `hide_title_on_card` → réservés admin) :

- Titre, slug, description courte, description longue (Markdown)
- Ce que vous apprendrez, prérequis
- ID vidéo trailer, méta-description, mots-clés
- Prix, thumbnail
- **Publié** (checkbox) → toggle brouillon/publié

### Builder de cours (modules, leçons, contenu)

L'instructeur accède au même builder que le staff, mais **uniquement pour ses propres cours**.

#### Gestion des modules

| Action | URL | Description |
|--------|-----|-------------|
| **Liste des modules** | `/manage/courses/<slug>/modules/` | Voir, créer, renommer, supprimer, réordonner (drag & drop) |
| **Renommer un module** | *(inline HTMX)* | Clic sur l'icône crayon → champ éditable inline |
| **Toggle brouillon module** | *(inline HTMX)* | Checkbox "Publié" dans le formulaire d'édition inline |
| **Supprimer un module** | *(inline HTMX)* | Confirmation "Sûr ?" avant suppression |
| **Réordonner** | *(drag & drop)* | SortableJS avec sauvegarde HTMX |

#### Gestion des leçons

| Action | URL | Description |
|--------|-----|-------------|
| **Liste des leçons d'un module** | `/manage/courses/<slug>/modules/<id>/lessons/` | Voir, créer, éditer, supprimer, réordonner |
| **Éditer une leçon** | *(inline HTMX)* | Titre, slug, gratuit (checkbox), publié (checkbox) |
| **Accéder au builder de contenu** | `/manage/course/<slug>/lesson/<slug>/` | Construire le contenu de la leçon |

#### Builder de contenu (blocs)

| Action | URL | Description |
|--------|-----|-------------|
| **Ajouter un bloc** | `/manage/block/add/<lesson_id>/<type>/` | Ajouter texte, vidéo, audio, fichier ou quiz |
| **Éditer un bloc** | `/manage/block/edit/<block_id>/` | Modifier le contenu d'un bloc |
| **Supprimer un bloc** | `/manage/block/delete/<block_id>/` | Supprimer un bloc (HTMX) |
| **Réordonner les blocs** | `/manage/block/reorder/` | Drag & drop SortableJS |
| **Prévisualiser le Markdown** | `/manage/preview-markdown/` | Rendu live du Markdown (HTMX) |

#### Quiz

| Action | URL | Description |
|--------|-----|-------------|
| **Ajouter une question** | `/manage/quiz/add-question/<block_id>/` | Texte, 4 choix (C/D optionnels), réponse correcte, explication, durée |
| **Supprimer une question** | `/manage/quiz/delete-question/<question_id>/` | Supprimer (HTMX) |

#### Landing Page Builder

| Action | URL | Description |
|--------|-----|-------------|
| **Gérer la landing page** | `/manage/courses/<slug>/landing/` | Vue d'ensemble de toutes les sections |
| **Ajouter une section** | `/manage/courses/<slug>/landing/add/<type>/` | Types : hero, text, image, video, features, text_image, faq, testimonials |
| **Éditer une section** | `/manage/landing/edit/<id>/` | Titre, contenu markdown, image, vidéo, sous-titre, CTA, position image, classes CSS, fond |
| **Supprimer une section** | `/manage/landing/delete/<id>/` | HTMX |
| **Dupliquer une section** | `/manage/landing/duplicate/<id>/` | Clone avec même image |
| **Toggle visibilité** | `/manage/landing/toggle/<id>/` | Masquer/afficher sans supprimer |
| **Réordonner** | `/manage/courses/<slug>/landing/reorder/` | Drag & drop |
| **Pré-remplir un template** | `/manage/courses/<slug>/landing/prefill/` | Crée 6 sections par défaut (hero, texte, features, text_image, témoignages, FAQ) |

### Statistiques

| Action | URL | Description |
|--------|-----|-------------|
| **Stats étudiants d'un cours** | `/manage/course/<slug>/stats/` | Progression de chaque étudiant (%, dernière activité) |

---

## 5. Superuser / Staff

### Tout ce que fait l'instructeur, plus :

#### Gestion centralisée des cours

| Action | URL | Description |
|--------|-----|-------------|
| **Liste de tous les cours** | `/manage/courses/` | Tous les cours (publiés ou non), recherche, tri, HTMX |
| **Créer un cours (admin)** | `/manage/courses/create/` | Formulaire complet avec `is_featured` et `hide_title_on_card` |
| **Supprimer un cours** | `/manage/courses/<slug>/delete/` | HTMX |

#### Django Admin (`/admin/`)

Accès complet à l'admin Django (Unfold) pour :

- **Utilisateurs** : créer, modifier, supprimer, changer les permissions
- **Cours / Modules / Leçons / Blocs** : CRUD complet
- **AccessRequest** : approuver/rejeter les demandes de paiement → déclenche l'email automatique
- **Coupons** : créer/modifier des codes promo (pourcentage, dates de validité)
- **Codes d'activation** : créer des codes à usage unique
- **InstructorRequest** : approuver/rejeter les demandes instructeur → crée le profil automatiquement
- **InstructorPlan** : gérer les offres (prix, limites, features)
- **InstructorProfile** : voir/modifier les profils instructeurs
- **Notifications** : voir toutes les notifications
- **Questions / Réponses support** : modérer

#### Prévisualisation

- **Forcer la vue landing** : ajouter `?view=landing` sur n'importe quel cours pour voir la page de vente même si on a accès
- **Voir le contenu brouillon** : le staff voit tout (modules, leçons non publiés) avec des badges "Brouillon" jaunes

#### Notifications automatiques

- Reçoit une notification quand un étudiant pose une nouvelle question support

---

## 6. Système de brouillon (Draft)

Le système de brouillon fonctionne à **3 niveaux** :

| Niveau | Champ | Par défaut |
|--------|-------|------------|
| **Cours** | `Course.is_published` | `False` (brouillon) |
| **Module** | `Module.is_published` | `True` (publié) |
| **Leçon** | `Lesson.is_published` | `True` (publiée) |

### Règles de visibilité

| Qui | Voit quoi |
|-----|-----------|
| **Étudiant** | Uniquement le contenu publié à tous les niveaux |
| **Instructeur (propriétaire)** | Tout son contenu, même en brouillon (avec badge jaune "Brouillon") |
| **Superuser / Staff** | Tout le contenu de tous les cours |

### Comportement détaillé

- **Cours non publié** : n'apparaît ni dans le catalogue ni sur la page d'accueil
- **Module non publié** : n'apparaît pas dans la liste des modules du cours (côté étudiant)
- **Leçon non publiée** : n'apparaît pas dans le sommaire ni dans la sidebar
- **Accès direct à une leçon brouillon** : l'étudiant est redirigé vers le cours avec un message d'erreur
- **Accès direct à une leçon dans un module brouillon** : même redirection

### Où toggler le brouillon

| Niveau | Où |
|--------|-----|
| **Cours** | Checkbox "Publier la formation" dans le formulaire de création/édition |
| **Module** | Checkbox "Publié" dans l'édition inline (icône crayon → formulaire) |
| **Leçon** | Checkbox "Publié" dans l'édition inline (icône crayon → formulaire) |

### Badges visuels (instructeur/staff uniquement)

- **Builder** : badge jaune "Brouillon" à côté des modules/leçons non publiés
- **Page du cours** : badge jaune "Brouillon" à côté des titres de modules/leçons
- **Sidebar leçon** : "(Brouillon)" en jaune à côté du titre

---

## 7. Système de paiement et accès

### Deux modes d'accès à un cours payant

#### Mode 1 : Preuve de paiement (CCP / BaridiMob)

1. L'étudiant va sur `/access/request/<course_id>/`
2. Upload d'une image de preuve de paiement (JPG/PNG, max 5 Mo)
3. Code promo optionnel (vérifié en HTMX avec le prix recalculé en temps réel)
4. Demande créée avec statut **PENDING**
5. L'admin approuve dans Django Admin → statut **APPROVED**
6. Signal → email automatique envoyé avec reçu PDF en pièce jointe
7. L'étudiant peut télécharger le reçu PDF à tout moment : `/access/receipt/<id>/`

#### Mode 2 : Code d'activation

1. L'étudiant va sur la même page `/access/request/<course_id>/`
2. Saisit un code d'activation (généré par l'admin)
3. Le code est vérifié avec `select_for_update()` (anti-race condition)
4. Si valide → accès immédiat (pas besoin d'approbation admin)

### Coupons

- Créés par l'admin dans Django Admin
- Code unique, pourcentage de réduction (1-100%)
- Dates de validité optionnelles (début/fin)
- Vérification en temps réel via HTMX sur la page de demande d'accès
- Le prix final est stocké dans `AccessRequest.final_price`

### Cas particuliers

- **Demande en attente** : l'étudiant voit une page "En attente de validation"
- **Demande rejetée** : l'étudiant peut re-soumettre avec une nouvelle preuve
- **Cours gratuit** (`price=0`) : accès automatique pour tous les utilisateurs connectés

### Reçu PDF

- Généré avec WeasyPrint
- Contient : nom de l'étudiant, formation, prix payé, date
- Envoyé par email et téléchargeable

---

## 8. Notifications

### Types de notifications automatiques

| Événement | Destinataire | Message |
|-----------|-------------|---------|
| Leçon terminée | Étudiant | "Leçon validée ✅" |
| Cours 100% complété | Étudiant | "Cours COMPLÉTÉ ! 🏆" |
| Réponse support reçue | Étudiant (auteur de la question) | "Nouvelle réponse Support 💬" |
| Nouvelle question support | Tous les superusers | "Nouvelle Question Élève 🙋‍♂️" |

### Interface

| Action | URL | Description |
|--------|-----|-------------|
| **Voir toutes les notifications** | `/notifications/` | Liste complète, les plus récentes en premier |
| **Cliquer sur une notification** | `/notifications/read/<id>/` | Marque comme lue et redirige vers le lien associé |
| **Marquer comme lue (HTMX)** | `/notifications/mark-read/<id>/` | Toggle lu/non-lu sans recharger la page |
| **Tout marquer comme lu** | `/notifications/mark-all/` | HTMX, met à jour le badge compteur |

### Badge dans la navbar

- Pastille rouge avec le nombre de notifications non lues
- Mis à jour automatiquement via HTMX (OOB swap)
- Dropdown avec les 10 dernières notifications (context processor)

---

## 9. Support / Questions

### Fonctionnement

1. L'étudiant pose une question depuis une leçon (formulaire en bas de page)
2. La question est liée au **cours** et à la **leçon** spécifique
3. Notification envoyée à tous les superusers
4. Le staff répond dans le fil de discussion
5. Notification envoyée à l'étudiant quand il reçoit une réponse
6. L'étudiant ou le staff peut marquer la question comme "Résolue"
7. Si l'auteur re-répond sur un ticket résolu → le ticket est rouvert

### URLs

| Action | URL | Description |
|--------|-----|-------------|
| **Poser une question** | `/support/ask/<lesson_id>/` | POST depuis la leçon |
| **Voir une discussion** | `/support/discussion/<question_id>/` | Fils de discussion complet |
| **Mes questions** | `/support/my-questions/` | Liste de mes questions (en cours + résolues) |
| **Marquer résolu** | `/support/resolve/<question_id>/` | Fermer le ticket |

### Statuts

| Statut | Signification |
|--------|--------------|
| **OPEN** | En attente de réponse |
| **RESOLVED** | Marqué comme résolu |
| **CLOSED** | Fermé |

---

## 10. SEO & Technique

### SEO

- **Sitemap XML** : `/sitemap.xml` — liste toutes les formations publiées (changefreq weekly, priority 0.8)
- **Meta description** : configurable par cours (max 160 caractères)
- **Mots-clés** : configurables par cours (séparés par des virgules)
- **Open Graph** : blocs template pour `og:title`, `og:description`, `og:image`
- **Slugs** : URLs propres basées sur les slugs

### Markdown

- Descriptions de cours, contenu des leçons, landing pages → tout est en **Markdown**
- Rendu avec le filtre template `|md`
- FAQ parsée automatiquement avec `|faq_items` (format question/réponse)

### Sécurité

- **CSRF** : tous les formulaires + HTMX (header automatique)
- **Upload sécurisé** : fichiers renommés en UUID, extensions validées, taille limitée
- **Race condition** : `select_for_update()` sur les codes d'activation et coupons
- **Permissions** : chaque vue builder vérifie l'ownership du cours (instructeur ≠ voir les cours des autres)
- **Accès leçon** : double vérification (brouillon + accès payé)

### Son de complétion

- Chaque cours peut avoir un son personnalisé (`completion_sound`)
- Joué quand l'étudiant termine une leçon
- Formats acceptés : MP3, WAV, OGG

---

## 11. Stack technique

| Technologie | Usage |
|-------------|-------|
| **Django 6.0.2** | Backend, ORM, vues, formulaires |
| **Python 3.12** | Langage serveur |
| **Django Cotton** | Composants réutilisables (17+ composants) |
| **Tailwind CSS v4.2** | Style (utilitaires, zéro CSS inline) |
| **Alpine.js** | Interactivité côté client (toggles, modals, accordéons) |
| **HTMX** | Requêtes AJAX, rechargement partiel, formulaires dynamiques |
| **SortableJS** | Drag & drop (modules, leçons, blocs, sections landing) |
| **Celery** | Tâches asynchrones (envoi d'emails) |
| **WeasyPrint** | Génération de PDF (reçus) |
| **Django Allauth** | Authentification (signup, login, password reset, email confirmation) |
| **Django Unfold** | Interface admin modernisée |
| **SQLite** | Base de données (dev) |
| **Bunny Stream** | Hébergement vidéo (par ID) |

### Structure des composants Cotton

Les composants sont dans `templates/cotton/` et organisés par catégorie :
- `ui/` : boutons, badges, éléments de base
- `layout/` : navbar, footer, flash messages
- `course/` : module accordion, lesson sidebar
- `manage/` : module item, lesson item (builder)
- `landing/` : sections de landing page
- `instructor/` : plan card