# Instructions pour les agents IA (Codex, Cursor, Copilot, Gemini…)

**Lis [`CONTRIBUTING.md`](CONTRIBUTING.md) en entier avant toute modification** : il décrit la stack, les règles d'or,
le catalogue des composants Cotton, les conventions de design, les garde-fous automatiques et les pièges connus.

Essentiel :

- Stack : Django 5.2 · django-cotton · HTMX 2 · Alpine 3 · Tailwind 4 (binaire standalone, pas de Node) · pytest/Playwright · Ruff.
- Interdits : `<style>`, `style=`, `on*=`, `<script>` avec code dans les templates ; balisage de bouton/carte/badge/titre/champ
  recréé à la main ; HTML construit en Python pour HTMX ; couleur d'interaction autre que `primary`.
- Obligatoires : composants Cotton, `Alpine.data` dans `static/js/components/` (chargé avant Alpine), services pour la logique métier,
  permissions vérifiées côté serveur, contenu utilisateur nettoyé, tests pour tout nouveau comportement.
- Commandes de vérification : `ruff check . && ruff format --check . && python manage.py makemigrations --check --dry-run && pytest`,
  et `python manage.py tailwind build` si des classes Tailwind changent.
- N'affaiblis jamais un garde-fou (`tests/test_hardening.py`, CI) pour « faire passer » : corrige la cause.
