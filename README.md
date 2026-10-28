# Hajime Learning

> 📘 **Développeurs et IA : lisez d'abord [`CONTRIBUTING.md`](CONTRIBUTING.md)** — stack, règles, composants, conventions et garde-fous.

Plateforme de formation en ligne (Django 5.2) : cours, quiz, progression, certificats, espace instructeur.

## Démarrage

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver                              # config.settings.dev par défaut
```

## Qualité

```bash
ruff check .                              # lint (règles dans ruff.toml)
ruff format .                             # formatage
pytest -m "not e2e" --cov                 # tests rapides + couverture (seuil dans .coveragerc)
playwright install chromium && pytest -m e2e   # tests navigateur (quiz, notes, auto-enregistrement…)
```

Les réglages de test sont dans `config/settings/test.py`. La CI GitHub (`.github/workflows/ci.yml`)
exécute lint, vérification des migrations, tests avec couverture et tests navigateur à chaque push.

## Organisation du code

| Dossier | Rôle |
| --- | --- |
| `courses/views/` | Vues par domaine : `student`, `builder`, `course_admin`, `landing` (+ `_helpers`) |
| `access/services.py`, `courses/services.py` | Règles métier (coupons, codes d'activation, complétion, quiz) : les vues restent fines |
| `config/throttle.py` | Limitation de débit (coupons, codes, contact) basée sur le cache |
| `courses/markdown.py` | Rendu Markdown **nettoyé** (nh3) — à utiliser pour tout contenu saisi par un utilisateur |
| `config/pdf.py` | Rendu PDF (xhtml2pdf) des templates, feuilles de style statiques comprises |
| `templates/cotton/` | Composants django-cotton (`<c-ui.btn />`, `<c-course.card />`…) |
| `templates/courses/{home,detail,lesson,manage}/` | Sections de pages incluses (`{% include %}`) |

## Front-end

Règle : **pas de `<style>`, `style=`, `onclick=` ni de `<script>` inline** (un test le vérifie).
Priorité à Tailwind, Alpine.js et HTMX, sous forme de composants Cotton.

- `static/css/app.css` : point d'entrée du CSS écrit à la main (`static/css/app/*.css`), hors Tailwind.
- `static/css/pdf/` : feuilles de style des PDF (reçu, certificat).
- `theme/static/css/dist/styles.css` : Tailwind compilé (`python manage.py tailwind start` / `build`).
- `static/js/components/` : composants Alpine (`Alpine.data`) chargés avant Alpine dans `base.html`.
- Boutons : `<c-ui.btn variant="…" />` (voir `static/css/app/buttons.css` et `DESIGN.md`) ; cartes : `<c-ui.card />`.
- Ombres dures : utilitaires `shadow-brutal-*` du thème Tailwind (`theme/static_src/src/styles.css`).
- Les réponses HTMX sont des **partiels de template** (jamais du HTML construit en Python).
- `static/js/builder/` : scripts du builder (éditeur de blocs, aperçu Markdown, SortableJS).
- `static/js/vendor/` : bibliothèques tierces minifiées (Alpine, HTMX, marked, SortableJS).

## Composants Cotton (`templates/cotton/`)

Règle : **jamais de balisage de carte, bouton, badge, titre ou champ écrit à la main dans une page** —
on utilise le composant (des tests le vérifient). Les styles « maison » vivent dans `static/css/app/*.css`
(couche `components`, donc surchargeables par les utilitaires Tailwind).

| Composant | Rôle | Styles |
| --- | --- | --- |
| `<c-ui.btn variant size block icon>` | Boutons et liens-boutons (primary, secondary, outline, accent, danger, ghost, inverse, toolbar) | `buttons.css` |
| `<c-ui.card variant padding drawn>` | Cartes (brutal, soft, flat, muted) | `cards.css` |
| `<c-ui.card-header icon title>` | En-tête de carte (titre + badge/action à droite) | — |
| `<c-ui.badge variant tone>` | Badges (tons solid, soft, dark) | `badges.css` |
| `<c-ui.title size as>` | Échelle de titres (lg, md, sm) | `typography.css` |
| `<c-ui.link>`, `<c-ui.kicker>`, `<c-ui.tape>`, `<c-ui.marquee>` | Lien de marque, sur-titre ruban, adhésif décoratif, bandeau défilant | — |
| `<c-ui.progress-bar>`, `<c-ui.alert>`, `<c-ui.avatar>`, `<c-ui.empty-state>`, `<c-ui.page-header>` | Éléments d'interface divers | `meter.css` |
| `<c-form.field :field label hint aside variant>` | Libellé + champ Django + erreur/aide ; `error`, `hint`, `check`, `checkbox-card`, `upload`, `input`, `select`, `textarea` | — |
| `<c-layout.container size>` | Conteneur de page centré | — |
| `<c-layout.navbar>`, `footer`, `nav-link`, `footer-link`, `social-link`, `auth-card`, `auth-switch`… | Structure du site | — |
| `<c-course.block-frame icon tone>` | Cadre repliable commun aux blocs de leçon (texte, vidéo, audio, fichier, Anki, quiz) | — |

Outil de non-régression visuelle : `SNAP_DIR=/tmp/avant pytest tests/snapshots.py` avant un refactor,
puis `SNAP_DIR=/tmp/apres SNAP_COMPARE=/tmp/avant pytest tests/snapshots.py` après (voir l'en-tête du fichier).

## Production (cPanel)

Variables d'environnement : voir l'en-tête de `config/settings/prod.py`
(`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DB_*`, **`SITE_URL`** (https, obligatoire), `EMAIL_*`).
Après chaque déploiement : `python manage.py migrate && python manage.py collectstatic --noinput`.
Les fichiers de cours payants et les certificats sont stockés hors de `media/` (`protected_media/`).
