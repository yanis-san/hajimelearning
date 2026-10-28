# Guide de contribution — règles et pratiques du projet

> **À lire en entier avant toute modification, par les développeurs comme par les IA.**
> Ces règles ne sont pas des préférences : la plupart sont vérifiées par des tests (§ 11) et la CI refuse
> le code qui les enfreint. Si une règle te gêne, change-la **ici et dans le test qui la protège** — jamais en la contournant.

## Sommaire

1. [La stack](#1-la-stack)
2. [Commandes](#2-commandes)
3. [Architecture](#3-architecture)
4. [Règles d'or](#4-règles-dor)
5. [Front-end : Cotton, Tailwind, Alpine, HTMX](#5-front-end--cotton-tailwind-alpine-htmx)
6. [Catalogue des composants](#6-catalogue-des-composants)
7. [Conventions de design](#7-conventions-de-design)
8. [Back-end Django](#8-back-end-django)
9. [Sécurité](#9-sécurité)
10. [Tests et qualité](#10-tests-et-qualité)
11. [Garde-fous automatiques](#11-garde-fous-automatiques)
12. [Pièges déjà rencontrés](#12-pièges-déjà-rencontrés)
13. [Workflow Git et CI](#13-workflow-git-et-ci)
14. [Checklist avant de livrer](#14-checklist-avant-de-livrer)
15. [Règles spécifiques aux IA](#15-règles-spécifiques-aux-ia)

---

## 1. La stack

| Couche | Technologie | Version | Rôle |
| --- | --- | --- | --- |
| Langage | Python | 3.13 en CI, 3.14 en local | |
| Framework | **Django** | 5.2 LTS (`5.2.x`) | Back-end, ORM, admin |
| Composants UI | **django-cotton** | 2.6 | Composants de templates (`<c-ui.btn />`) |
| Interactivité serveur | **HTMX** + `django-htmx` | 2.0.8 / 1.27 | Échanges HTML partiels, pas de SPA |
| Interactivité locale | **Alpine.js** | 3.14 (bundle avec plugins Collapse, Intersect…) | État local, `Alpine.data` |
| Styles | **Tailwind CSS** | 4.1 (binaire *standalone* via `django-tailwind`) | Utilitaires + thème dans `@theme` |
| Glisser-déposer | SortableJS | 1.15 | Réordonnancement du builder |
| Markdown | `markdownx` + `Markdown` + **`nh3`** | | Rendu **nettoyé** (anti-XSS) |
| Auth | `django-allauth` | 65 | Connexion par e-mail, vérification obligatoire |
| Admin | `django-unfold` | 0.71 | Back-office |
| Tâches | Celery (mode *eager* en prod cPanel) | 5.6 | PDF, e-mails |
| PDF | `xhtml2pdf` | 0.2 | Reçus et certificats |
| Statiques | WhiteNoise (manifest + compression en prod) | | |
| BDD | SQLite (dev/test) · MySQL via PyMySQL (prod cPanel) | | |
| Qualité | **Ruff** (lint + format), pytest, pytest-cov, Playwright | | Voir `ruff.toml`, `.coveragerc` |

Principes de la stack : **rendu côté serveur**, JavaScript minimal et localisé, **pas de build JS** (pas de Node,
pas de bundler), composants réutilisables, tout vérifié par des tests.

## 2. Commandes

```bash
# Environnement
python -m venv .venv && source .venv/Scripts/activate        # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver                                   # réglages config.settings.dev

# CSS — OBLIGATOIRE dès que des classes Tailwind changent dans un template, un .py ou un .js
python manage.py tailwind build                              # ou `tailwind start` en développement
#   → régénère theme/static/css/dist/styles.css (fichier versionné : à commiter)

# Qualité (identique à la CI)
ruff check . && ruff format --check .
python manage.py makemigrations --check --dry-run
pytest -m "not e2e" --cov                                    # tests rapides + couverture (seuil 83 %)
playwright install chromium && pytest -m e2e                 # tests navigateur

# Non-régression visuelle (avant / après un refactor d'interface)
SNAP_DIR=/tmp/avant pytest tests/snapshots.py -p no:cacheprovider
SNAP_DIR=/tmp/apres SNAP_COMPARE=/tmp/avant pytest tests/snapshots.py -p no:cacheprovider
```

Production : `python manage.py migrate && python manage.py collectstatic --noinput` à chaque déploiement.
Variables d'environnement : en-tête de `config/settings/prod.py` (`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
`DB_*`, `SITE_URL`, `EMAIL_*`).

## 3. Architecture

```
config/                 réglages (base / dev / prod / test), urls, celery, throttle.py, pdf.py
  settings/test.py      réglages de la suite de tests (jamais de sys.argv pour détecter les tests)
courses/                cours, modules, leçons, blocs, quiz, progression, certificats
  views/                UNE vue = UN fichier de domaine : student, builder, course_admin, landing, _helpers
  services.py           règles métier de la progression (complétion, certificat, quiz)
  markdown.py           rendu Markdown nettoyé — seul point d'entrée pour du contenu saisi
  progress.py           calcul de progression (source de vérité, version « en lot » pour le dashboard)
  permissions.py        accès au builder, portée des objets gérés
access/                 coupons, demandes de paiement, codes d'activation (+ services.py)
instructors/ support/ notifications/ contact/ users/
templates/
  cotton/               COMPOSANTS (ui, form, layout, course, manage, notification, support, instructor)
  courses/{home,detail,lesson}/   sections de pages incluses par {% include %} (pas réutilisables)
  courses/manage/       studio : builder, formulaires, partiels HTMX
static/
  css/app.css           point d'entrée du CSS écrit à la main → static/css/app/*.css
  css/pdf/              feuilles de style des PDF
  js/components/        composants Alpine (Alpine.data)  — un fichier par composant
  js/builder/           scripts du studio
  js/vendor/            bibliothèques tierces minifiées (ne jamais modifier)
theme/static_src/src/styles.css   source Tailwind : @theme (couleurs, ombres), animations
theme/static/css/dist/styles.css  CSS compilé (généré — ne JAMAIS l'éditer à la main)
tests/                  suite pytest ; snapshots.py = outil visuel (non collecté)
```

**Vue** = HTTP uniquement (permissions, paramètres, choix du template). **Service** = règle métier.
**Modèle** = données et invariants. **Template** = présentation. Ne mélange pas.

## 4. Règles d'or

Ces dix règles résument tout. Le reste du document les détaille.

1. **Jamais de `<style>`, `style="…"`, `onclick=`/`on*=` ni de `<script>` avec du code dans un template.**
   Seuls `<script src>` et `<script type="application/json">` sont admis. (Test.)
2. **Composants Cotton partout.** Un bouton, une carte, un badge, un titre, un champ de formulaire, un libellé,
   une barre de progression = un composant. On ne recrée jamais leur balisage. (Tests.)
3. **Tailwind d'abord**, CSS écrit à la main seulement si Tailwind ne peut pas l'exprimer
   (animations, motifs, états complexes) — alors dans `static/css/app/<sujet>.css`.
4. **Alpine pour l'état local, HTMX pour parler au serveur.** Pas de `fetch` maison quand HTMX suffit.
5. **Les réponses HTMX sont des partiels de template**, jamais du HTML construit en Python.
6. **Une couleur d'interaction : `primary`.** Pas d'orange, pas de couleur « décorative » sur les liens et boutons.
   Au survol on assombrit **la même teinte**, on ne change jamais de couleur.
7. **Vues fines, logique dans les `services.py`.** Statuts en `TextChoices`, contraintes en `UniqueConstraint`.
8. **Aucun contenu saisi par un utilisateur n'est affiché sans nettoyage** (`courses.markdown`, échappement Django).
9. **Toute portée d'accès est vérifiée côté serveur** (`get_managed_course`, querysets filtrés) — jamais « par ID brut ».
10. **Rien n'est fini sans test ni CI verte**, et `ruff` + `makemigrations --check` propres.

## 5. Front-end : Cotton, Tailwind, Alpine, HTMX

### 5.1 Cotton (composants)

- Fichiers dans `templates/cotton/<dossier>/<nom_snake>.html` ; appel **en kebab-case** :
  `templates/cotton/ui/card_header.html` → `<c-ui.card-header>`. Les balises avec `_` sont interdites (test).
- Déclare les propriétés et leurs défauts avec `<c-vars nom="défaut" />`. Tout ce qui n'est pas déclaré
  atterrit dans `{{ attrs }}` : **toujours** le poser sur l'élément racine (`{{ attrs }}`) pour permettre `id`, `x-data`, `title`…
- Le contenu est `{{ slot }}` ; les zones nommées s'écrivent `<c-slot name="title">…</c-slot>` et se lisent `{{ title }}`.
- Un composant **doit être utilisé** : un composant orphelin fait échouer les tests. Supprime-le plutôt que de le laisser.
- **Piège majeur** : sur une balise `<c-…>`, un attribut qui commence par `:` est interprété par Cotton (variable du
  template). Pour Alpine, écris `x-bind:class`, `x-bind:disabled`, `x-on:click` (ou `@click`), **jamais** `:class`.
  Sur un élément HTML ordinaire, `:class` reste valide.
- Valeurs dynamiques : `:field="form.title"` (variable) ; chaînes avec logique :
  `variant="{% if ok %}primary{% else %}outline{% endif %}"`.
- Dans l'attribut `class` d'un composant, **les utilitaires Tailwind surchargent** les styles du composant
  (les styles maison sont dans la couche `components`, inférieure à `utilities`). Garde cette propriété.
- `{% include %}` pour une **section de page** non réutilisable (`courses/home/*`, `courses/detail/*`) ;
  composant Cotton dès qu'un balisage est réutilisable ou paramétrable.

### 5.2 Tailwind v4

- **Aucune valeur arbitraire répétée** : couleurs et ombres passent par `@theme`
  (`theme/static_src/src/styles.css`). Ombres dures : `shadow-brutal-sm | brutal | brutal-md | brutal-lg | brutal-xl`,
  `shadow-soft`. N'écris pas `shadow-[4px_4px_0_0_#111827]`.
- Tailwind détecte les classes **littérales** : ne construis jamais un nom de classe par concaténation
  (`"bg-" + couleur`) — écris des `{% if %}` avec les classes complètes.
- Après tout changement de classes : `python manage.py tailwind build` puis commit du `dist/styles.css`.
- Mobile d'abord (`sm:`, `md:`, `lg:`). Aucune page ne doit déborder horizontalement à 390 px (test e2e, police large).

### 5.3 CSS écrit à la main (`static/css/app/`)

- Point d'entrée `static/css/app.css` ; **un fichier = une responsabilité** : `base`, `patterns`, `animations`,
  `buttons`, `cards`, `badges`, `typography`, `meter`.
- Les styles de composants sont importés dans la couche Tailwind : `@import url("app/xxx.css") layer(components);`
  → ils restent surchargeables par les utilitaires. Ne mets pas de `!important` (sauf les formes « manga » existantes).
- Les variantes passent par des **variables CSS** (`--btn-bg`, `--badge-fg`…), pas par des dizaines de classes.
- Pas de build : fichiers servis tels quels (WhiteNoise gère le manifest en prod).

### 5.4 Alpine.js

- **État d'une ligne** (`{ open: false }`) : inline, c'est l'usage normal.
- **Dès qu'il y a de la logique** (méthodes, `init`, `fetch`, plus de ~3 lignes) : composant dans
  `static/js/components/<nom>.js` avec `Alpine.data('nom', (args) => ({…}))`, **déclaré dans `templates/base.html`
  AVANT `alpine.min.js`** (Alpine démarre dès son chargement et rate les composants enregistrés après).
- Les données serveur vont dans le composant par **arguments** (`x-data="quiz('quiz-data-12', '/url')"`) ou
  `<script type="application/json">` (`json_script`) — jamais en générant du JavaScript depuis le template.
- Cookie CSRF : lis-le dans le JS (`csrftoken`, non `HttpOnly` volontairement) ; ne le rends pas dans le template.

### 5.5 HTMX

- Le corps de `<body>` porte `hx-headers` avec le jeton CSRF : toutes les requêtes HTMX l'envoient.
- **Réponse = template partiel** (`render(request, 'x/partials/y.html', …)`). Pour mettre à jour un second élément,
  utilise `hx-swap-oob` **dans le template** (voir `block_saved.html`, `read_response.html`).
- **Aucun contenu à renvoyer** (réordonnancement…) → `HttpResponse(status=204)`.
- Données de contrôle côté client → en-tête de réponse `HX-Trigger` (JSON) ; écoute l'évènement avec Alpine
  (`x-on:builder-saved="…"`). Auto-enregistrement du builder : voir `block-editor.js` + `_save_block_response`.
- Si tu modifies `hx-post`/`hx-get` en JavaScript, **appelle `htmx.process(element)`** : htmx lit l'URL à l'initialisation.
- Erreur de validation HTMX : renvoie un statut 4xx **sans corps à substituer** (htmx ne remplace pas sur 4xx) et
  gère `htmx:responseError` côté composant.

## 6. Catalogue des composants

| Composant | Propriétés | Quand l'utiliser |
| --- | --- | --- |
| `<c-ui.btn>` | `variant` primary·secondary·outline·accent·danger·ghost·inverse·toolbar · `size` xs·sm·md·lg · `href` · `type` · `block` · `icon` · `disabled` | **Tout** bouton ou lien-bouton |
| `<c-ui.card>` | `variant` brutal·soft·flat·muted · `padding` none·xs·sm·md·lg·xl · `drawn` · `class` | Tout panneau/encadré |
| `<c-ui.card-header>` | `icon` · `title` · slot (badge/action à droite) | En-tête d'une carte du studio |
| `<c-ui.badge>` | `variant` gray·primary·green·blue·yellow·orange·red·purple · `tone` solid·soft·dark | Étiquettes et statuts |
| `<c-ui.title>` | `size` lg·md·sm · `as` h1·h2·h3 | **Tous** les titres de page (échelle unique) |
| `<c-ui.link>` | `href` | Lien textuel de marque |
| `<c-ui.kicker>` · `<c-ui.tape>` · `<c-ui.marquee>` (+`marquee-item`) | | Décors « manga » de la vitrine |
| `<c-ui.progress-bar>` | `percent` · `color` · `size` · `show_label` · `manga` | Toute progression (`<progress>`) |
| `<c-ui.alert>` · `avatar` · `empty-state` · `page-header` · `logo` | | Éléments d'interface |
| `<c-form.field>` | `:field` · `label` · `hint` · `aside` · `required` · `variant` caps·plain·compact · slot = contrôle personnalisé | **Tout** champ de formulaire Django (libellé + champ + erreur/aide) |
| `<c-form.label>` · `error` · `hint` | | Briques de `field` ; libellé isolé |
| `<c-form.check>` · `checkbox-card` · `upload` | | Cases, cases-cartes, zones d'upload |
| `<c-form.input>` · `select` · `textarea` · `coupon-field` | | Champs non liés à un `form` Django |
| `<c-layout.container>` | `size` md·lg·2xl·3xl·4xl·5xl·6xl·7xl | **Toute** page : largeur + marges responsives |
| `<c-layout.navbar>` · `footer` · `nav-link` · `footer-link` · `footer-heading` · `social-link` · `auth-card` · `auth-switch` · `flash-messages` · `admin-card` · `course-builder` | | Structure du site |
| `<c-course.block-frame>` | `icon` · `tone` · slot `title` · slot `footer` | Cadre commun des blocs de leçon |
| `<c-course.block-text>` · `block-video` · `block-audio` · `block-file` · `block-anki` · `block-quiz` | `block` | Un composant par type de bloc ; chacun s'appuie sur `block-frame` |
| `<c-course.card>` · `module-accordion` · `lesson-sidebar` · `landing-section` · `block-note` | | Pages de cours |
| `<c-manage.block-item>` · `course-row` · `furigana-guide` · `landing-section-item` · `lesson-item` · `module-item` · `quiz-question-item` · `sort-header` | | Studio de création (listes triables, édition en ligne) |
| `<c-notification.dropdown>` · `item` | | Cloche et liste de notifications |
| `<c-support.question-row>` · `reply-card` | | Questions et réponses |
| `<c-instructor.plan-card>` | | Offres instructeur |

**Ajouter un composant** : (1) vérifie qu'aucun existant ne convient ou ne peut être étendu par une propriété ;
(2) crée `templates/cotton/<dossier>/<nom>.html` avec `<c-vars>` + `{{ attrs }}` ; (3) mets ses styles dans
`static/css/app/` si besoin ; (4) **utilise-le** immédiatement ; (5) ajoute-le à ce tableau et au README.

## 7. Conventions de design

Source visuelle : le style « manga / néo-brutaliste » (contours encre, ombres dures, bords dessinés).

- **Couleurs** : `primary` `#E6003A` (contraste 4,75:1 avec le blanc, **ne pas l'éclaircir**), `primary-dark` `#B30030`
  (survols et **texte rose sur fond clair**), encre `#111827`. États : vert (succès), rouge (danger/erreur),
  jaune (alerte/outils du studio), bleu (information). **Plus d'orange.**
- **Texte** : jamais `text-gray-400` ni plus clair sur fond clair (2,5:1) → `text-gray-500` minimum. Sur fond sombre
  (pied de page, barres de gestion) `gray-400` est correct. Texte rose sur fond clair : `text-primary` seulement si
  le fond est blanc ; sur fond teinté (`bg-primary/10`) → `text-primary-dark`.
- **Boutons** — règle absolue : *une variante = une teinte, le survol assombrit la même teinte*
  (pas de jaune→rouge, noir→rose, rose→blanc). `primary` = action principale (une par zone) ; `secondary` = action forte
  secondaire ; `outline` = neutre ; `accent` (jaune) = **outils de gestion/builder réservés staff et instructeurs** ;
  `danger` = destructif ; `ghost` = discret ; `inverse` = sur fond sombre/coloré ; `toolbar` = barres de gestion.
  Survol : `translateY(-2px)` + ombre agrandie ; clic : enfoncé. Source : `static/css/app/buttons.css`.
- **Cartes** : `brutal` (panneaux principaux), `soft` (info), `flat` (imbriqué), `muted` (encart). Pas de variante ad hoc.
- **Titres** : `<c-ui.title>` (lg éditorial, md applicatif, sm section). Les titres de la page d'accueil (`courses/home/*`)
  gardent des styles éditoriaux propres à chaque section : c'est volontaire.
- **Formulaires** : `<c-form.field>` ; variante `caps` pour le studio, `plain` pour les formulaires courants,
  `compact` pour les grilles denses. Erreurs avec `<c-form.error>`, aides avec `<c-form.hint>`.
- **Accessibilité** : ratios WCAG AA (testés pour la marque), `aria-label` sur les boutons-icônes, focus visible
  (contour rose), `<progress>` natif, jamais d'information portée par la couleur seule.
- **Langue** : le site est en français, textes écrits directement (pas de `gettext` : décision assumée tant qu'il n'y a
  qu'une langue). Si une seconde langue arrive, la migration se fait en une passe globale, pas à moitié.

## 8. Back-end Django

- **Vues** (`courses/views/*`) : décorateurs d'accès, lecture des paramètres, appel du service, rendu. Rien d'autre.
  Une vue = une responsabilité ; on ajoute dans le fichier de domaine adapté, pas dans un « fourre-tout ».
- **Services** (`access/services.py`, `courses/services.py`) : règles métier, transactions (`@transaction.atomic`),
  erreurs métier par exceptions dédiées (`AccessError`, `InvalidScore`) affichables telles quelles.
  Les effets de bord différés (tâche Celery) passent par `transaction.on_commit`.
- **Modèles** : statuts en `models.TextChoices` (`AccessRequest.Status.APPROVED`, jamais `'APPROVED'`) ;
  unicité par `UniqueConstraint(name=…)` (jamais `unique_together`) ; **index** sur les colonnes filtrées en permanence ;
  méthodes de domaine sur le modèle (`Coupon.discounted_price`).
- **Requêtes** : `select_related`/`prefetch_related` systématiques, **zéro N+1**. Pour plusieurs objets,
  une version « en lot » (voir `get_courses_progress`). Mises à jour multiples : `bulk_update`.
- **Ordre** : `apply_order(queryset, ids)` avec un queryset **déjà restreint** à ce que l'utilisateur gère.
- **Permissions du studio** : `builder_access_required`, `get_managed_course(user, slug)`, `get_managed_course_from_*`.
  Limites d'offre instructeur : `plan_limit_reached` (le staff n'est jamais limité).
- **Limitation de débit** : `config.throttle.allow(request, 'scope', limit, window)` sur toute action devinable
  (coupons, codes, formulaires publics). Cache partagé en prod (`FileBasedCache`).
- **PDF** : `config.pdf.render_pdf(template, ctx)` ; CSS dans `static/css/pdf/` (xhtml2pdf ne supporte pas tout CSS).
- **Fichiers payants et certificats** : `ProtectedStorage` (hors `MEDIA_ROOT`), servis par une vue qui contrôle l'accès.
- **Réglages** : `base` (commun) · `dev` · `prod` · `test`. Jamais de détection de contexte par `sys.argv`.
  Pas de secret dans le code ; variables d'environnement en prod.
- **Migrations** : toute modification de modèle → `makemigrations` (la CI vérifie). Ne modifie pas une migration
  déjà appliquée ; les données de référence passent par une migration de données (`RunPython`).
- **Style** : Ruff (`ruff.toml`). Pas de `except Exception` large sans journalisation, pas d'import dans une fonction
  sauf cycle d'import avéré, noms explicites (pas de `l`, `I`).

## 9. Sécurité

- **Markdown/HTML utilisateur** : rendu **uniquement** via `courses.markdown.render_markdown_safe` (nh3, liste blanche).
  `mark_safe` sur du contenu non nettoyé est interdit. Textes courts : filtre `|furigana` (échappe avant de convertir).
- **IDOR** : tout objet modifiable est retrouvé **via le cours géré** (`course=course`), jamais par un simple `id`.
- **CSRF** : actif partout ; HTMX via `hx-headers`, JS via le cookie.
- **Accès aux contenus** : `user_has_access` ; téléchargements protégés par vue ; reçus réservés à l'étudiant concerné
  et aux demandes **approuvées**.
- **Entrées numériques** (score de quiz…) : validées côté serveur, jamais crues.
- **Dépendances** : surveille Dependabot ; épingle les versions dans `requirements*.txt` ; la CI installe depuis zéro.
- **Pages d'accès par force brute** : throttle (voir § 8).

## 10. Tests et qualité

- `pytest.ini` + `config/settings/test.py` : Celery *eager*, e-mails en mémoire, hachage rapide, médias jetables
  (nettoyés en fin de session), cache vidé entre les tests.
- **Marqueurs** : `e2e` (Playwright). `pytest -m "not e2e"` en local pour aller vite.
- **Où écrire un test** : règle métier → test du service ; vue → `client` Django ; JavaScript/Alpine/HTMX réel →
  `tests/test_e2e.py` ; garde-fou de convention → `tests/test_hardening.py` ; rendu de pages → `tests/test_pages_smoke.py`.
- Une correction de bug **commence par un test qui échoue**.
- **Couverture** : seuil 83 % (`.coveragerc`) ; ne le baisse jamais, remonte-le quand elle progresse.
- **Tests e2e** : `live_server`, connexion par cookie de session (`login_as`), police large imposée pour la mise en page.
- **Refactor d'interface** : capture avant/après avec `tests/snapshots.py` ; comprends chaque différence
  (le bruit connu : horodatages, lecteurs vidéo, dates relatives).

## 11. Garde-fous automatiques

Ces tests protègent les règles ci-dessus — ils **échouent** si tu les enfreins :

| Test | Règle protégée |
| --- | --- |
| `test_no_inline_style_or_script_in_templates` | Pas de `<style>`, `style=`, `onclick=`, `<script>` avec code |
| `test_every_template_compiles` | Aucun template (composants compris) ne contient d'erreur de syntaxe |
| `TestComponentUsage` | Pas de carte, de `<h1>`, de libellé, de `<label>`/`<progress>` écrits à la main ; balises `c-*` en kebab-case ; aucun composant inutilisé |
| `TestDesignConvention` | Plus d'orange ; boutons via `c-ui.btn` |
| `TestAccessibilityContrast` | Contraste WCAG AA de la marque ; pas de `text-gray-400` sur fond clair |
| `test_no_horizontal_overflow_on_mobile` (e2e) | Aucune page ne déborde à 390 px |
| `TestDocumentationInSync` | Ce guide liste chaque composant Cotton ; `CLAUDE.md` et `AGENTS.md` pointent vers lui |
| `TestReorderScope`, `TestPlanLimits`, `TestThrottling`, `TestMarkdownSanitization`… | Sécurité et règles métier |
| CI : `ruff check`, `ruff format --check`, `makemigrations --check`, couverture ≥ 83 % | Qualité du code |

## 12. Pièges déjà rencontrés

1. **Attribut `class` en double** (`class` dans le template + `{{ attrs }}`) : le navigateur ignore le second. Déclare `class=""`
   dans `<c-vars>` et rends `{{ class }}` (voir `ui/badge.html`).
2. **`:class` sur une balise `<c-…>`** : Cotton l'interprète comme une variable → `x-bind:class`.
3. **Composant Alpine enregistré après Alpine** : il n'existe pas au démarrage → toujours avant `alpine.min.js`.
4. **`hx-post` modifié en JS sans `htmx.process`** : l'ancienne URL continue d'être utilisée (doublons de blocs).
5. **`transaction.on_commit` dans un test** : ne s'exécute pas sans `django_capture_on_commit_callbacks`.
6. **Un bloc de template jamais exercé peut casser une page entière** (`{% endif %}` manquant 6 mois) :
   le test de compilation de tous les templates existe pour ça — ne le retire pas.
7. **Ruff `F401` supprime les `import x.signals`** des `apps.ready()` : garde `# noqa: F401`.
8. **Texte de couleur fixée par une classe d'un composant** : les utilitaires Tailwind passés via `class=` gagnent
   (couche `utilities` > `components`) — utile, mais ne compte pas sur l'ordre du fichier CSS.
9. **Polices** : une mise en page qui tient avec Inter peut déborder avec une police de repli plus large → le test e2e
   impose Verdana/DejaVu ; teste toujours le pire cas.
10. **Le CSS compilé est versionné** : oublier `tailwind build` = classes absentes en production.

## 13. Workflow Git et CI

- Branche de travail → PR vers `main` (ou commit direct pour un projet solo), **jamais de code non testé**.
- Messages de commit : `type(portée): résumé` en français (`feat`, `fix`, `refactor`, `style`, `test`, `ci`, `docs`, `chore`).
  Un commit = une idée ; sépare refactor et correction de bug.
- La CI (`.github/workflows/ci.yml`) exécute **lint**, **migrations à jour**, **tests + couverture**, **e2e Playwright**.
  Elle doit être verte avant de fusionner. Elle installe depuis `requirements-dev.txt` : toute dépendance ajoutée y va,
  épinglée, **et résolvable sur Linux/Python 3.13**.
- Ne commite jamais `db.sqlite3`, `media/`, `protected_media/`, `cache/`, `.env` (déjà ignorés).

## 14. Checklist avant de livrer

- [ ] `ruff check . && ruff format --check .` propres
- [ ] `python manage.py makemigrations --check --dry-run` : aucune migration manquante
- [ ] `python manage.py tailwind build` lancé si des classes ont changé (et `dist/styles.css` commité)
- [ ] `pytest` vert (dont `-m e2e` si l'interface ou le JS a changé)
- [ ] Nouveau comportement testé ; bug corrigé = test de non-régression
- [ ] Aucun style/script inline, aucun balisage de composant recréé, aucune couleur hors convention
- [ ] Mobile vérifié (390 px) ; contraste respecté
- [ ] Permissions et validation côté serveur ; contenu utilisateur nettoyé
- [ ] README / ce guide / catalogue des composants mis à jour si une règle ou un composant change

## 15. Règles spécifiques aux IA

1. **Lis ce fichier en entier avant d'écrire du code**, puis `README.md`. `DESIGN.md` décrit l'intention visuelle
   (partiellement ancienne) ; en cas de contradiction, **ce guide et le code font foi**.
2. **Ne contourne jamais un garde-fou** : n'affaiblis pas un test, n'ajoute pas de `# noqa` ou d'exception pour faire passer
   la CI, ne supprime pas un test qui échoue. Corrige la cause, ou demande une décision humaine pour changer la règle.
3. **Cherche avant de créer** : un composant, un helper (`_helpers.py`), un service ou un test similaire existe probablement.
4. **Modifications minimales et ciblées** : pas de reformatage hors périmètre, pas de renommage opportuniste.
5. **Vérifie par l'exécution**, pas par supposition : lance les tests, le lint, `tailwind build`, et pour l'interface
   les captures (`tests/snapshots.py`) ou un test e2e. Ne déclare jamais « ça marche » sans l'avoir exécuté.
6. **Ne touche pas** à `static/js/vendor/*`, `theme/static/css/dist/styles.css` (régénéré), aux migrations existantes.
7. **Ne change pas les conventions de design** (couleurs, variantes de boutons, échelle de titres) sans demande explicite ;
   si tu en as besoin d'une nouvelle, ajoute-la au composant concerné, documente-la ici et teste-la.
8. **Sécurité par défaut** : toute nouvelle vue vérifie les permissions, borne les objets au cours géré, valide ses entrées,
   et limite le débit si l'action est devinable.
9. **Garde les fins de ligne et l'encodage** : fichiers UTF-8 ; ne convertis pas massivement les fins de ligne.
10. **Dis ce qui n'est pas fait** : si tu n'as pas pu vérifier quelque chose, ou si tu as fait un compromis, écris-le
    clairement dans ta réponse.
