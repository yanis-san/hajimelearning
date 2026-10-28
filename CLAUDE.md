# Hajime Learning — instructions pour Claude Code

@CONTRIBUTING.md

## Rappel express (détails dans CONTRIBUTING.md)

- Stack : Django 5.2 · django-cotton · HTMX 2 · Alpine 3 · Tailwind 4 (standalone, **pas de Node**) · pytest/Playwright · Ruff.
- Jamais de style/script inline ; **composants Cotton partout** (`templates/cotton/`) ; réponses HTMX = partiels de template.
- Vues fines, règles métier dans `services.py`, statuts en `TextChoices`, contenu utilisateur nettoyé (`courses/markdown.py`).
- Après un changement de classes Tailwind : `python manage.py tailwind build`.
- Avant de conclure : `ruff check . && ruff format --check . && python manage.py makemigrations --check --dry-run && pytest`.
- Ne contourne ni n'affaiblis jamais un test de `tests/test_hardening.py` : ils protègent les conventions du projet.
