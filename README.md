# Hajime Learning

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

## Production (cPanel)

Variables d'environnement : voir l'en-tête de `config/settings/prod.py`
(`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DB_*`, `SITE_URL`, `EMAIL_*`).
Après chaque déploiement : `python manage.py migrate && python manage.py collectstatic --noinput`.
Les fichiers de cours payants et les certificats sont stockés hors de `media/` (`protected_media/`).
