# Cahier des charges — Composants Django Cotton
## Hajime Learning

> **Stack obligatoire :** Django Cotton (composants) · Tailwind CSS (style) · Alpine.js (interactivité client) · HTMX (interactivité serveur)  
> **Règles absolues :** Zéro `style="..."` inline · Zéro `<script>` ou `onclick="..."` inline · Tout passe par Cotton + Tailwind + Alpine.js

---

## Structure des dossiers

```
templates/cotton/
├── layout/
│   ├── navbar.html
│   ├── footer.html
│   └── flash-messages.html
├── ui/
│   ├── btn.html
│   ├── badge.html
│   ├── avatar.html
│   ├── alert.html
│   ├── progress-bar.html
│   ├── empty-state.html
│   └── page-header.html
├── form/
│   ├── input.html
│   ├── textarea.html
│   ├── select.html
│   └── coupon-field.html
├── course/
│   ├── card.html
│   ├── lesson-sidebar.html
│   ├── module-accordion.html
│   ├── block-text.html
│   ├── block-video.html
│   ├── block-audio.html
│   ├── block-file.html
│   └── block-quiz.html
├── notification/
│   ├── dropdown.html
│   └── item.html
└── support/
    ├── question-card.html
    └── reply-card.html
```

---

## Priorités de création

| Priorité | Groupe | Raison |
|---|---|---|
| 1 | UI Primitives | Bloquants pour tous les autres composants |
| 2 | Formulaires | Utilisés dans login, signup, profil, accès |
| 3 | Layout | Refactoring de `base.html` |
| 4 | Cours | Cœur fonctionnel de la plateforme |
| 5 | Notifications | Transversal, présent dans navbar |
| 6 | Support | Moins prioritaire, fonctionnel isolé |

---

## Groupe 1 — Layout

Ces trois composants **remplacent les blocs actuellement hardcodés dans `base.html`**.

---

### `cotton/layout/navbar.html`

**Utilisé dans :** `templates/base.html`  
**Props :** aucune (accède au contexte global `user`, `navbar_notifications`, `navbar_unread_count`)  
**Slot :** aucun

**Contenu à encapsuler :**
- Logo + liens de navigation desktop
- Menu hamburger mobile (Alpine.js `x-data="{ mobileOpen: false }"`)
- Dropdown notifications (délégué au composant `c-notification-dropdown`)
- Avatar + lien profil (délégué au composant `c-avatar`)
- Bouton déconnexion (formulaire POST)
- Boutons connexion/inscription si anonyme

**Technos :**
- Alpine.js : toggle menu mobile (`x-show`, `@click`)
- HTMX : aucun directement (le dropdown notifications délègue)

---

### `cotton/layout/footer.html`

**Utilisé dans :** `templates/base.html`  
**Props :** aucune  
**Slot :** aucun

**Contenu :**
- Copyright `&copy; 2025 Hajime Learning`
- Liens CGV, Contact

---

### `cotton/layout/flash-messages.html`

**Utilisé dans :** `templates/base.html`  
**Props :** aucune (lit `messages` du contexte Django)  
**Slot :** aucun

**Comportement :**
- Affiche les messages Django (`success`, `error`, `info`)
- Couleurs : vert pour success, rouge pour error, bleu pour info
- Auto-dismiss via Alpine.js après 4 secondes (`x-data`, `x-init`, `setTimeout`)
- Icônes SVG selon le type (pas d'emoji)

---

## Groupe 2 — UI Primitives

---

### `cotton/ui/btn.html`

**Utilisé dans :** partout (login, course_list, course_detail, lesson_detail, builder, profile, support…)

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `variant` | `primary` | `primary` · `secondary` · `outline` · `danger` · `ghost` |
| `href` | `""` | Si rempli → `<a>`, sinon → `<button>` |
| `type` | `button` | `button` · `submit` · `reset` |
| `size` | `md` | `sm` · `md` · `lg` |
| `disabled` | `false` | Désactive le bouton |

**Slot :** contenu du bouton (texte, icône SVG)  
**`{{ attrs }}` :** oui — pour passer `hx-*`, `@click`, `class` supplémentaire  

**Variantes visuelles :**
- `primary` → `bg-orange-500 text-white hover:bg-orange-600`
- `secondary` → `bg-gray-900 text-white hover:bg-gray-700`
- `outline` → `border border-gray-300 text-gray-700 bg-white hover:bg-gray-50`
- `danger` → `bg-red-500 text-white hover:bg-red-600`
- `ghost` → `text-gray-600 hover:bg-gray-100`

---

### `cotton/ui/badge.html`

**Utilisé dans :** `courses/lesson_detail.html` (type de bloc), `courses/manage/partials/block_list.html`, `support/question_detail.html` (statut OPEN/RESOLVED), `notifications/`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `variant` | `gray` | `green` · `red` · `blue` · `orange` · `gray` · `yellow` |

**Slot :** texte du badge  

**Visuels :**
- Petit, arrondi (`rounded-full`), padding `px-2.5 py-0.5`, texte `text-xs font-medium`
- `green` → `bg-green-100 text-green-800`
- `red` → `bg-red-100 text-red-800`
- `blue` → `bg-blue-100 text-blue-800`
- `orange` → `bg-orange-100 text-orange-700`
- `gray` → `bg-gray-100 text-gray-600`
- `yellow` → `bg-yellow-100 text-yellow-800`

---

### `cotton/ui/avatar.html`

**Utilisé dans :** `layout/navbar.html`, `users/profile.html`, `courses/manage/students_stats.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `user` | — | Objet User Django |
| `size` | `md` | `sm` (6) · `md` (8) · `lg` (16) · `xl` (24) (taille en unités Tailwind) |
| `href` | `""` | Si rempli, l'avatar est un lien `<a>` |

**Comportement :**
- Si `user.avatar` → affiche l'image avec `object-cover rounded-full`
- Sinon → cercle `bg-orange-500` avec initiale `user.first_name|first|upper`

---

### `cotton/ui/progress-bar.html`

**Utilisé dans :** `courses/course_detail.html`, `courses/dashboard.html`, `courses/manage/students_stats.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `percent` | `0` | Valeur numérique 0–100 |
| `color` | `orange` | `orange` · `green` · `red` · `blue` |
| `show_label` | `true` | Affiche ou non le `%` à droite |

**Note :** la `width` dynamique (`style="width: X%"`) est l'**unique exception** au zéro inline — c'est du Tailwind dynamique impossible autrement.

---

### `cotton/ui/empty-state.html`

**Utilisé dans :** `courses/course_list.html`, `courses/dashboard.html`, `notifications/list.html`, `support/my_questions.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `icon` | `📭` | Emoji ou SVG |
| `title` | `Rien ici` | Titre principal |
| `message` | `""` | Sous-titre/description |

**Slot :** optionnel — bouton CTA en dessous du message

---

### `cotton/ui/page-header.html`

**Utilisé dans :** `courses/course_list.html`, `courses/dashboard.html`, `users/profile.html`, `support/my_questions.html`, `courses/manage/students_stats.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `title` | — | Titre de la page |
| `subtitle` | `""` | Sous-titre optionnel |

**Slot :** optionnel — actions alignées à droite (boutons, liens)

---

### `cotton/ui/alert.html`

**Utilisé dans :** pages de succès/erreur (`access/request_success.html`, `access/request_pending.html`, pages de reset mot de passe)

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `variant` | `info` | `info` · `success` · `warning` · `error` |
| `title` | `""` | Titre optionnel en gras |
| `dismissible` | `false` | Bouton de fermeture Alpine.js |

**Slot :** corps du message

---

## Groupe 3 — Formulaires

---

### `cotton/form/input.html`

**Utilisé dans :** `account/login.html`, `account/signup.html`, `account/password_reset*.html`, `users/profile.html`, `access/request_form.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `name` | — | Attribut `name` de l'input |
| `type` | `text` | `text` · `email` · `password` · `tel` · `date` · `number` · `file` |
| `label` | `""` | Label affiché au-dessus |
| `placeholder` | `""` | Placeholder |
| `value` | `""` | Valeur initiale |
| `error` | `""` | Message d'erreur (rouge sous le champ) |
| `required` | `false` | Attribut required |
| `help_text` | `""` | Texte d'aide gris sous le champ |

**Comportement spécial :**
- Si `type="password"` → bouton œil Alpine.js pour toggle visibilité (`x-data="{ show: false }"`, `:type="show ? 'text' : 'password'"`)
- Si `type="file"` → style adapté (pas d'input classique)
- Si `error` rempli → bordure rouge + message d'erreur en `text-red-500 text-xs`

---

### `cotton/form/textarea.html`

**Utilisé dans :** `support/question_detail.html` (formulaire réponse), `courses/lesson_detail.html` (formulaire question)

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `name` | — | Attribut `name` |
| `label` | `""` | Label |
| `placeholder` | `""` | Placeholder |
| `value` | `""` | Valeur initiale |
| `error` | `""` | Message d'erreur |
| `rows` | `4` | Nombre de lignes |

---

### `cotton/form/select.html`

**Utilisé dans :** `account/signup.html`, `users/profile.html` (pays, ville, genre)

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `name` | — | Attribut `name` |
| `label` | `""` | Label |
| `error` | `""` | Message d'erreur |
| `selected` | `""` | Valeur sélectionnée |

**Slot :** les `<option>` à l'intérieur du `<select>`

---

### `cotton/form/coupon-field.html`

**Utilisé dans :** `access/request_form.html` uniquement

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `validate_url` | — | URL de validation HTMX |
| `target` | `#price-result` | Cible HTMX pour afficher le résultat |

**Comportement :**
- Input texte + bouton "Appliquer"
- `hx-post="{{ validate_url }}"` sur l'input (trigger `keyup changed delay:500ms`) ou sur le bouton
- `hx-target="{{ target }}"`, `hx-swap="innerHTML"`

---

## Groupe 4 — Cours

---

### `cotton/course/card.html`

**Utilisé dans :** `courses/course_list.html`, `courses/dashboard.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `course` | — | Objet `Course` Django |
| `show_progress` | `false` | Afficher la barre de progression (dashboard) |
| `progress` | `0` | Pourcentage si `show_progress` |

**Contenu :**
- Thumbnail (ou placeholder emoji)
- Titre, `short_description` (2 lignes max, `line-clamp-2`)
- Badge prix (Gratuit / X DA)
- Bouton "Voir le cours" → `course.get_absolute_url()`
- Si `show_progress` → `c-progress-bar`

---

### `cotton/course/lesson-sidebar.html`

**Utilisé dans :** `courses/lesson_detail.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `course` | — | Objet `Course` avec prefetch modules/leçons |
| `current_lesson` | — | Leçon active |
| `completed_ids` | `""` | IDs des leçons complétées (pour les coches ✅) |

**Contenu :**
- Header avec titre du cours
- Liste des modules en accordion (délègue à `c-course-module-accordion`)
- Chaque leçon : icône ✅/⭕, titre cliquable, état actif surligné

**Alpine.js :** `x-data` pour l'état ouvert/fermé de chaque module

---

### `cotton/course/module-accordion.html`

**Utilisé dans :** `cotton/course/lesson-sidebar.html`, `courses/course_detail.html` (landing)

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `module` | — | Objet `Module` avec leçons |
| `open` | `false` | Ouvert par défaut |
| `current_lesson` | `""` | ID leçon active (pour ouvrir auto le bon module) |

**Alpine.js :** `x-data="{ open: {{ open }} }"`, `@click` sur le header, `x-show` sur le body

---

### `cotton/course/block-text.html`

**Utilisé dans :** `courses/lesson_detail.html`  
**Props :** `block` (objet `ContentBlock`)  
**Contenu :** rendu Markdown (`block.content|markdownify`)

---

### `cotton/course/block-video.html`

**Utilisé dans :** `courses/lesson_detail.html`  
**Props :** `block`  
**Contenu :** iframe YouTube responsive (`aspect-video`), URL construite depuis `block.youtube_video_id`

---

### `cotton/course/block-audio.html`

**Utilisé dans :** `courses/lesson_detail.html`  
**Props :** `block`  
**Contenu :**
- Player audio natif `<audio controls>`
- Bouton "Afficher/Masquer la correction" → Alpine.js `x-data="{ showCorrection: false }"`, `x-show`

---

### `cotton/course/block-file.html`

**Utilisé dans :** `courses/lesson_detail.html`  
**Props :** `block`  
**Contenu :** lien téléchargement avec icône, nom du fichier, attribut `download`

---

### `cotton/course/block-quiz.html`

**Utilisé dans :** `courses/lesson_detail.html`  
**Props :** `block` (avec questions prefetch)  
**Contenu :** jeu de quiz complet Alpine.js

**États Alpine.js (`x-data`) :**
```js
{
  state: 'start',          // start | playing | feedback | time_up | end
  currentIndex: 0,
  score: 0,
  selectedAnswer: null,
  isCorrect: null,
  timeLeft: 0,
  timer: null,
  questions: [...],        // passées depuis le template Django
  // méthodes: startQuiz, selectAnswer, nextQuestion, endQuiz, saveScore (fetch)
}
```

**Transitions entre états :**
- `start` → bouton "Démarrer" → `playing`
- `playing` → réponse sélectionnée → `feedback`
- `feedback` → "Suivant" → `playing` ou `end`
- Timer à 0 → `time_up`
- `end` → save score via `fetch` + affichage résultat

---

## Groupe 5 — Notifications

---

### `cotton/notification/dropdown.html`

**Utilisé dans :** `cotton/layout/navbar.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `notifications` | `""` | QuerySet des dernières notifications |
| `unread_count` | `0` | Nombre non lues (badge rouge) |

**Alpine.js :** `x-data="{ open: false }"`, `@click.outside="open = false"`, `x-transition` (scale + opacity)  
**HTMX :** formulaire "Tout marquer comme lu" (`hx-post` → `mark_all_read`)  
**Contenu :** liste de `c-notification-item`, lien "Tout voir"

---

### `cotton/notification/item.html`

**Utilisé dans :** `cotton/notification/dropdown.html`, `notifications/list.html`, `notifications/partials/single_notification.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `notif` | — | Objet `Notification` |
| `compact` | `false` | Version compacte (dropdown) vs complète (liste) |

**HTMX :** bouton toggle lu/non-lu → `hx-post`, `hx-swap="outerHTML"` (se remplace lui-même)  
**Alpine.js :** `@click.stop` pour empêcher la propagation sur le bouton toggle

---

## Groupe 6 — Support

---

### `cotton/support/question-card.html`

**Utilisé dans :** `support/my_questions.html`, `courses/lesson_detail.html` (liste des questions de l'étudiant sur la leçon)

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `question` | — | Objet `Question` |
| `show_course` | `false` | Afficher le cours d'origine |

**Contenu :**
- Titre question, extrait message
- Badge statut (`c-badge` : `OPEN` → blue, `RESOLVED` → green)
- Date, lien vers `question_detail`

---

### `cotton/support/reply-card.html`

**Utilisé dans :** `support/question_detail.html`

**Props (`<c-vars>`) :**
| Prop | Défaut | Description |
|---|---|---|
| `reply` | — | Objet `Reply` |
| `is_staff` | `false` | Style différent (fond orange léger) si réponse staff |

**Contenu :**
- Avatar + nom de l'auteur (`c-avatar`)
- Corps du message (Markdown si applicable)
- Date relative (`timesince`)
- Badge "Staff" si `is_staff`

---

## Récapitulatif — 22 composants

| # | Composant | Groupe | Alpine.js | HTMX |
|---|---|---|---|---|
| 1 | `layout/navbar` | Layout | ✅ | — |
| 2 | `layout/footer` | Layout | — | — |
| 3 | `layout/flash-messages` | Layout | ✅ (auto-dismiss) | — |
| 4 | `ui/btn` | UI | — | via `{{ attrs }}` |
| 5 | `ui/badge` | UI | — | — |
| 6 | `ui/avatar` | UI | — | — |
| 7 | `ui/alert` | UI | ✅ (dismiss) | — |
| 8 | `ui/progress-bar` | UI | — | — |
| 9 | `ui/empty-state` | UI | — | — |
| 10 | `ui/page-header` | UI | — | — |
| 11 | `form/input` | Form | ✅ (password toggle) | — |
| 12 | `form/textarea` | Form | — | — |
| 13 | `form/select` | Form | — | — |
| 14 | `form/coupon-field` | Form | — | ✅ |
| 15 | `course/card` | Course | — | — |
| 16 | `course/lesson-sidebar` | Course | ✅ | — |
| 17 | `course/module-accordion` | Course | ✅ | — |
| 18 | `course/block-text` | Course | — | — |
| 19 | `course/block-video` | Course | — | — |
| 20 | `course/block-audio` | Course | ✅ | — |
| 21 | `course/block-file` | Course | — | — |
| 22 | `course/block-quiz` | Course | ✅ (complet) | ✅ (save score) |
| 23 | `notification/dropdown` | Notification | ✅ | ✅ |
| 24 | `notification/item` | Notification | ✅ | ✅ |
| 25 | `support/question-card` | Support | — | — |
| 26 | `support/reply-card` | Support | — | — |
