# Cahier des charges — Composants & Pages — Phase 2

---

## 1. État des lieux

### ✅ Composants créés

| Composant | Fichier | Statut |
|---|---|---|
| Bouton universel | `cotton/ui/btn.html` | ✅ |
| Badge | `cotton/ui/badge.html` | ✅ |
| Avatar | `cotton/ui/avatar.html` | ✅ |
| Alerte / Flash | `cotton/ui/alert.html` | ✅ |
| Barre de progression | `cotton/ui/progress_bar.html` | ✅ |
| État vide | `cotton/ui/empty_state.html` | ✅ |
| En-tête de page | `cotton/ui/page_header.html` | ✅ |
| Champ input | `cotton/form/input.html` | ✅ |
| Textarea | `cotton/form/textarea.html` | ✅ |
| Select | `cotton/form/select.html` | ✅ |
| Item notification | `cotton/notification/item.html` | ✅ |
| Dropdown notifications | `cotton/notification/dropdown.html` | ✅ |
| Navbar | `cotton/layout/navbar.html` | ✅ |
| Footer | `cotton/layout/footer.html` | ✅ |
| Flash messages | `cotton/layout/flash_messages.html` | ✅ |
| Carte auth (layout) | `cotton/layout/auth_card.html` | ✅ |
| Carte cours | `cotton/course/card.html` | ✅ |

**Total : 17 composants créés**

---

### ✅ Pages refactorisées

| Template | Statut |
|---|---|
| `base.html` | ✅ |
| `courses/course_list.html` | ✅ |
| `account/login.html` | ✅ |
| `account/signup.html` | ✅ |
| `account/password_reset.html` | ✅ |
| `account/password_reset_done.html` | ✅ |
| `account/password_reset_from_key.html` | ✅ |
| `account/password_reset_from_key_done.html` | ✅ |

---

### ❌ Pages non refactorisées

| Template | Priorité | Notes |
|---|---|---|
| `courses/dashboard.html` | HAUTE | Dashboard étudiant : mes cours + progression |
| `courses/course_detail.html` | HAUTE | Page de vente d'un cours (landing page) |
| `courses/lesson_detail.html` | HAUTE | Lecteur de leçon avec blocs de contenu |
| `users/profile.html` | MOYENNE | Profil utilisateur, édition infos |
| `support/my_questions.html` | MOYENNE | Liste des questions de l'étudiant |
| `support/question_detail.html` | MOYENNE | Thread Q&A d'une question |
| `notifications/list.html` | BASSE | Page liste complète des notifications |
| **`courses/manage/builder.html`** | HAUTE | **Interface builder admin (cf section 3)** |
| **`courses/manage/students_stats.html`** | MOYENNE | **Stats étudiants par cours** |
| **`courses/manage/partials/*.html`** | HAUTE | **Tous les partials HTMX du builder** |

---

## 2. Composants restants à créer

### 2.1 Coté étudiant (lecture de cours)

#### `cotton/course/lesson_sidebar.html`
Barre latérale gauche dans la page `lesson_detail.html`.

**Props :**
- `course` — objet Course avec `modules__lessons` prefetchés
- `current_lesson` — leçon active
- `completed_ids` — liste d'IDs de leçons terminées

**Comportement :**
- Liste tous les modules avec leurs leçons en accordéon Alpine
- Chaque leçon affiche une coche verte si `lesson.id in completed_ids`
- Leçon active mise en surbrillance (orange)
- Cadenas si `not lesson.is_free and not has_access`
- Mobile : panneau latéral masqué par défaut, togglable via bouton hamburger

---

#### `cotton/course/module_accordion.html`
Utilisé dans `course_detail.html` (page de vente — programme du cours).

**Props :**
- `module` — objet Module avec ses leçons
- `index` — numéro du module (pour l'ouverture auto du premier)

**Comportement :**
- Alpine `x-data="{ open: index === 0 }"` — premier module ouvert par défaut
- Header clickable : titre du module + nombre de leçons + durée (si dispo)
- Corps : liste des leçons avec icône cadenas ou coche selon `is_free`

---

#### `cotton/course/block_text.html`
Bloc de contenu texte/Markdown dans la leçon.

**Props :**
- `block` — objet ContentBlock de type `text`

**Rendu :**
- `{{ block.text_content | markdownify }}` avec prose Tailwind (`prose prose-gray max-w-none`)
- Titre du bloc en `h3` si présent
- Fond blanc, padding généreux, bordure gauche orange subtile

---

#### `cotton/course/block_video.html`
Bloc vidéo Bunny Stream.

**Props :**
- `block` — objet ContentBlock de type `video`
- `library_id` — settings.BUNNY_LIBRARY_ID (passé depuis la vue)

**Rendu :**
- `<iframe>` embed Bunny Player responsive (aspect-ratio 16/9)
- Titre du bloc si présent
- Fond noir pour le player, arrondis subtils autour

---

#### `cotton/course/block_audio.html`
Bloc audio MP3 sécurisé.

**Props :**
- `block` — objet ContentBlock de type `audio`

**Rendu :**
- Lecteur `<audio controls>` stylisé Tailwind (pas le lecteur natif brut)
- Titre du fichier audio, icône micro-onde orange
- Fichier associé (correction) : bouton téléchargement secondaire si présent

---

#### `cotton/course/block_file.html`
Bloc fichier à télécharger.

**Props :**
- `block` — objet ContentBlock de type `file`

**Rendu :**
- Carte avec icône document, nom du fichier, bouton télécharger (`<c-ui.btn variant="outline">`)
- Badge indiquant le type de fichier (PDF, DOCX…)

---

#### `cotton/course/block_quiz.html`
Bloc quiz interactif.

**Props :**
- `block` — objet ContentBlock de type `quiz`
- `user` — `request.user`

**Comportement :**
- Alpine `x-data` pour gérer les réponses sélectionnées, score, état (en cours / terminé)
- Chaque question : `QuizQuestion` avec `question_text`, `option_a/b/c/d`, `correct_answer`
- Soumission : `fetch()` Alpine vers `save_quiz_result` (endpoint JSON existant)
- Affichage score final en orange
- Si déjà répondu (`QuizResult` existant) : affiche le score précédent avec date

---

### 2.2 Formulaires

#### `cotton/form/coupon_field.html`
Champ de saisie de code coupon avec validation HTMX en temps réel.

**Props :**
- `course` — pour passer le `course.id` à l'endpoint
- `name` — nom du champ (default: `code`)

**Comportement :**
- Input + bouton "Appliquer" dans une même ligne (flex)
- `hx-post` sur le bouton → endpoint de validation coupon → retourne un partial
- Zone de résultat HTMX : alerte verte (valide + % de réduction) ou rouge (invalide)
- Alpine : `x-data="{ applied: false }"` pour désactiver le champ une fois appliqué

---

### 2.3 Support

#### `cotton/support/question_card.html`
Carte d'une question dans `my_questions.html`.

**Props :**
- `question` — objet Question avec `lesson`, `status`, `created_at`, `replies count`

**Rendu :**
- Titre de la question, leçon associée (badge), date
- Badge statut : `open` (orange) / `resolved` (vert)
- Nombre de réponses, lien vers `question_detail`

---

#### `cotton/support/reply_card.html`
Carte d'une réponse dans `question_detail.html`.

**Props :**
- `reply` — objet Reply
- `is_staff` — booléen pour afficher le badge "Équipe"

**Rendu :**
- Avatar + nom auteur + date
- Badge orange "Équipe Hajime" si `is_staff`
- Contenu Markdown avec `prose`
- Fond légèrement différent si c'est la réponse du staff (gris très clair)

---

## 3. Interface Admin / Course Builder

### Contexte

La création et gestion des cours pour les **admins (staff)** passe par :
1. L'admin Django natif (pour créer Course, Module, Lesson)
2. Une interface custom `manage/builder.html` pour remplir le contenu des leçons (blocs)
3. Une vue `manage/students_stats.html` pour suivre la progression des étudiants

Ces interfaces actuelles n'utilisent pas nos composants Cotton. Elles doivent être refactorisées.

---

### 3.1 Nouveau layout admin : `cotton/layout/admin_card.html`

Layout wrapper partagé pour toutes les pages admin custom.

**Props :**
- `title` — titre de la page
- `subtitle` — sous-titre optionnel
- `breadcrumb` — slot optionnel pour fil d'Ariane

**Structure :**
- Header avec breadcrumb (Cours > Module > Leçon)
- Fond gris très clair `bg-gray-50 min-h-screen`
- Contenu dans un container `max-w-7xl mx-auto px-6 py-8`
- Barre latérale actions (slot) optionnelle

---

### 3.2 Builder de leçon : `courses/manage/builder.html`

Interface principale de création du contenu d'une leçon.

**Contexte actuel :** template HTML brut sans composants, sans style charte.

**Refactorisation cible :**

```
┌─────────────────────────────────────────────────────┐
│ BREADCRUMB : Cours > Module > Leçon                 │
├─────────────────────────────────────────────────────┤
│ PAGE HEADER : "Builder — [Leçon.title]"             │
│ sous-titre : module parent + badge publié/brouillon  │
├──────────────────────────┬──────────────────────────┤
│  LISTE DES BLOCS         │  PALETTE D'AJOUT         │
│  (sortable HTMX drag)    │  [+ Texte] [+ Vidéo]     │
│                          │  [+ Audio] [+ Fichier]   │
│  ┌──────────────────┐    │  [+ Quiz]                │
│  │ Bloc 1 (Texte)   │    │                          │
│  │ [✏️ Edit] [🗑️]  │    │  Card info leçon :       │
│  └──────────────────┘    │  - is_free toggle        │
│  ┌──────────────────┐    │  - ordre dans module     │
│  │ Bloc 2 (Vidéo)   │    │  - lien preview leçon    │
│  │ [✏️ Edit] [🗑️]  │    │                          │
│  └──────────────────┘    │                          │
└──────────────────────────┴──────────────────────────┘
```

**Composants à utiliser :**
- `<c-layout.admin-card>` pour le wrapper
- `<c-ui.page-header>` pour le titre
- `<c-ui.btn>` pour les boutons de la palette
- `<c-ui.badge>` pour le type de bloc (Texte, Vidéo…)
- Drag & Drop : Alpine + `hx-post` vers `update_block_order` existant

---

### 3.3 Partial : `cotton/manage/block_item.html`

Carte d'un bloc dans la liste du builder (remplace `partials/block_list.html`).

**Props :**
- `block` — objet ContentBlock
- `lesson` — pour les URLs HTMX

**Rendu :**
- Badge type (Texte / Vidéo / Audio / Fichier / Quiz) avec couleurs distinctes
- Titre du bloc ou "(sans titre)"
- Boutons : Éditer (`hx-get` → `partials/block_form.html`) + Supprimer (`hx-delete` + confirmation Alpine)
- Poignée drag & drop (icône 6 points, curseur grab)

---

### 3.4 Partial : `cotton/manage/block_form.html`

Formulaire d'ajout/édition d'un bloc (chargé en HTMX dans une modale ou panneau latéral).

**Props :**
- `form` — ContentBlockForm Django
- `block_type` — `text|video|audio|file|quiz`
- `lesson` — objet Lesson
- `block` — optionnel (si édition)

**Comportement Alpine :**
- `x-show` conditionnel selon `block_type` pour n'afficher que les champs pertinents
- Champ `text_content` : textarea avec preview Markdown en live (2 colonnes)
- Champ `video_id` : preview embed YouTube/Bunny live (`x-model` + iframe)
- Champ `file_content` : `<c-form.input type="file">`

---

### 3.5 Partial : `cotton/manage/quiz_question_item.html`

Carte d'une question de quiz dans le builder.

**Props :**
- `question` — objet QuizQuestion
- `block` — pour les URLs HTMX

**Rendu :**
- Texte de la question + 4 options (A/B/C/D)
- Bonne réponse surlignée en vert
- Bouton supprimer (`hx-delete` + confirm Alpine)

---

### 3.6 Page stats étudiants : `courses/manage/students_stats.html`

Tableau de bord de suivi des étudiants d'un cours.

**Contexte actuel :** template HTML brut.

**Refactorisation cible :**

```
┌─────────────────────────────────────────────────────┐
│ BREADCRUMB : Cours > Étudiants                      │
│ PAGE HEADER : "Étudiants — [Course.title]"          │
│              [X] étudiants inscrits                 │
├─────────────────────────────────────────────────────┤
│ Tableau responsive :                                │
│ Avatar | Nom | Progression  | Complété | Dernière   │
│             | [====  60%]   | 12/20    | activité   │
└─────────────────────────────────────────────────────┘
```

**Composants à utiliser :**
- `<c-ui.avatar>` pour chaque étudiant
- `<c-ui.progress-bar>` pour la progression
- `<c-ui.badge>` pour le niveau (débutant/avancé si défini)
- `<c-ui.page-header>` pour le titre

---

## 4. Nouvelles vues admin à créer (en plus du builder existant)

Ces vues n'existent pas encore — elles sont nécessaires pour gérer les cours sans passer par l'admin Django natif.

| Vue | URL | Description |
|---|---|---|
| Liste des cours admin | `/manage/courses/` | Tableau de tous les cours avec actions rapides |
| Créer un cours | `/manage/courses/create/` | Formulaire Course complet |
| Éditer un cours | `/manage/courses/<slug>/edit/` | Même formulaire pré-rempli |
| Gérer les modules | `/manage/courses/<slug>/modules/` | Ajouter/réordonner/supprimer modules |
| Gérer les leçons | `/manage/courses/<slug>/modules/<id>/lessons/` | Ajouter/réordonner/supprimer leçons |

### 4.1 `cotton/manage/course_row.html`
Ligne du tableau de gestion des cours.

**Props :** `course`

**Rendu :**
- Thumbnail miniature + titre + slug
- Badge publié/brouillon (`is_published`)
- Prix ou "Gratuit"
- Boutons : Builder / Étudiants / Éditer / Supprimer
- Tout en HTMX (inline delete avec confirmation Alpine)

---

### 4.2 `cotton/manage/module_item.html`
Item d'un module dans la gestion inline (sortable).

**Props :** `module`, `course`

**Rendu :**
- Titre du module, nombre de leçons
- Boutons : Ajouter leçon / Éditer titre / Supprimer
- Poignée drag & drop

---

## 5. Récapitulatif priorisation

### Sprint 1 — Cœur apprenant (priorité absolue)
1. ❌ `cotton/course/block_text.html`
2. ❌ `cotton/course/block_video.html`
3. ❌ `cotton/course/block_audio.html`
4. ❌ `cotton/course/block_file.html`
5. ❌ `cotton/course/block_quiz.html`
6. ❌ `cotton/course/lesson_sidebar.html`
7. ❌ Refacto `courses/lesson_detail.html`

### Sprint 2 — Page de vente & Dashboard
1. ❌ `cotton/course/module_accordion.html`
2. ❌ Refacto `courses/course_detail.html`
3. ❌ Refacto `courses/dashboard.html`

### Sprint 3 — Interface admin / Builder
1. ❌ `cotton/layout/admin_card.html`
2. ❌ `cotton/manage/block_item.html`
3. ❌ `cotton/manage/block_form.html`
4. ❌ `cotton/manage/quiz_question_item.html`
5. ❌ Refacto `courses/manage/builder.html`
6. ❌ Refacto `courses/manage/students_stats.html`
7. ❌ Nouvelles vues : liste cours admin, créer/éditer cours, modules/leçons

### Sprint 4 — Support, Profil, Notifications
1. ❌ `cotton/support/question_card.html`
2. ❌ `cotton/support/reply_card.html`
3. ❌ `cotton/form/coupon_field.html`
4. ❌ Refacto `support/my_questions.html`
5. ❌ Refacto `support/question_detail.html`
6. ❌ Refacto `users/profile.html`
7. ❌ Refacto `notifications/list.html`
