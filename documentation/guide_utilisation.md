# Guide d'utilisation — Hajime Learning

---

## 1. Accès au site

| Rôle | Comment y accéder |
|---|---|
| **Visiteur** | Accédez à `/` (page d'accueil) |
| **Étudiant** | Créez un compte via `/accounts/signup/` puis connectez-vous |
| **Admin / Staff** | Connectez-vous avec un compte `is_staff=True` |

Pour créer un super-utilisateur :
```bash
python manage.py createsuperuser
```

---

## 2. Parcours visiteur (anonyme)

| Action | URL |
|---|---|
| Voir le catalogue | `/` |
| Voir le détail d'un cours (page de vente) | `/course/<slug>/` |
| Voir une leçon gratuite | `/course/<slug>/lesson/<slug>/` |
| Se connecter | `/accounts/login/` |
| S'inscrire | `/accounts/signup/` |
| Mot de passe oublié | `/accounts/password/reset/` |

---

## 3. Parcours étudiant (connecté)

| Action | URL |
|---|---|
| Mon tableau de bord (mes cours) | `/dashboard/` |
| Demander l'accès à un cours payant | `/access/request/<course_id>/` |
| Suivre une leçon | `/course/<slug>/lesson/<slug>/` |
| Marquer une leçon comme terminée | Bouton "Terminer et continuer" dans la leçon |
| Répondre à un quiz | Directement dans la leçon |
| Poser une question au support | Formulaire en bas de chaque leçon |
| Voir mes questions support | `/support/my-questions/` |
| Consulter un thread de discussion | `/support/discussion/<id>/` |
| Mes notifications | `/notifications/` |
| Mon profil | `/users/profile/` |
| Télécharger un reçu de paiement | `/access/receipt/<id>/` |

---

## 4. Parcours admin / staff

### 4.1 Interface Django Admin

> URL : `/admin/`

C'est ici que l'on **crée les cours, modules et leçons**.

#### Créer un cours complet :

1. **`/admin/courses/course/add/`** — Créer le cours
   - Remplir : titre, slug, description courte, description longue (Markdown), prix, image
   - Cocher "Publié" quand le cours est prêt
   - Les **modules** se créent en inline directement sur cette page

2. **`/admin/courses/module/`** — Gérer les modules (ou via l'inline du cours)
   - Chaque module a un ordre et un titre
   - Les **leçons** se créent en inline directement sur la page module

3. **`/admin/courses/lesson/`** — Gérer les leçons (ou via l'inline du module)
   - Titre, slug, ordre, cocher "Gratuit" pour les leçons d'aperçu

#### Ajouter du contenu à une leçon (Builder) :

4. **Depuis le site** : Ouvrez n'importe quelle leçon en étant connecté en staff → cliquez sur le bandeau jaune **"✏️ Mode Édition"** en haut
   - Ou directement : `/manage/course/<slug>/lesson/<slug>/`

5. Dans le **Builder** vous pouvez :
   - Ajouter des blocs : Texte, Vidéo, Audio, Fichier, Quiz
   - Réordonner les blocs (drag & drop)
   - Éditer / supprimer chaque bloc
   - Pour les Quiz : ajouter des questions (QCM avec timer)

#### Gérer les accès étudiants :

| Action | Où |
|---|---|
| Approuver/rejeter les demandes d'accès | `/admin/access/accessrequest/` → colonne "Status" éditable en liste |
| Créer un code promo | `/admin/access/coupon/add/` |
| Créer un code d'activation | `/admin/access/activationcode/add/` |
| Voir les stats étudiants d'un cours | `/manage/course/<slug>/stats/` |

#### Gérer le support :

| Action | Où |
|---|---|
| Voir toutes les questions | `/admin/support/question/` |
| Répondre à une question | `/support/discussion/<id>/` (sur le site, pas dans l'admin) |
| Marquer comme résolu (en masse) | `/admin/support/question/` → action "Marquer comme Résolu" |

---

## 5. Résumé des flux principaux

### Flux : Étudiant achète un cours payant
```
Catalogue → Page du cours → "Débloquer l'accès"
→ Formulaire de demande (preuve CCP/BaridiMob OU code promo OU code activation)
→ Admin approuve dans /admin/access/accessrequest/
→ Étudiant voit le cours dans son dashboard
```

### Flux : Étudiant suit un cours
```
Dashboard → Cours → Module → Leçon
→ Lire le contenu (texte, vidéo, audio, fichier)
→ Répondre aux quiz
→ "Terminer et continuer" → Leçon suivante
→ Progression visible sur la page du cours
```

### Flux : Admin crée un cours
```
/admin/ → Cours → Ajouter
→ Remplir les infos + créer les modules (inline)
→ Pour chaque module → créer les leçons (inline)
→ Pour chaque leçon → ouvrir le Builder (via le site)
→ Ajouter les blocs de contenu
→ Publier le cours (cocher is_published)
```
