from django.core.management.base import BaseCommand
from django.utils.text import slugify
from courses.models import Course, Module, Lesson, ContentBlock, QuizQuestion


class Command(BaseCommand):
    help = "Seed le cours 1 : Le système d'écriture japonais"

    def handle(self, *args, **options):
        # ─── COURS ────────────────────────────────────────────
        course, created = Course.objects.update_or_create(
            slug='le-systeme-decriture-japonais',
            defaults={
                'title': "Le système d'écriture japonais",
                'short_description': (
                    "Maîtrisez les bases de la prononciation japonaise : les 5 voyelles, "
                    "les consonnes, le tableau des 50 sons (Gojuon) et le rythme syllabique."
                ),
                'description': (
                    "## Prononciation et système d'écriture japonais — Cours 1\n\n"
                    "Ce cours est le **point de départ idéal** pour apprendre le japonais. "
                    "Avant de tracer votre premier caractère, vous devez comprendre comment "
                    "la langue **sonne** et comment elle fonctionne à l'oral.\n\n"
                    "### Ce que vous allez apprendre :\n"
                    "- Les **5 voyelles** fondamentales (a, i, u, e, o)\n"
                    "- Les consonnes et leurs **exceptions**\n"
                    "- Le **tableau des 50 sons** (Gojuon) — la pièce maîtresse\n"
                    "- Le **rythme syllabique** unique du japonais\n"
                    "- Des **exercices audio** pour entraîner votre oreille\n\n"
                    "À l'origine, le japonais était une langue 100 % orale, sans le moindre "
                    "système d'écriture. Nous commençons donc tout naturellement par la base : "
                    "**la prononciation**."
                ),
                'what_you_will_learn': (
                    "- Prononcer correctement les 5 voyelles japonaises\n"
                    "- Connaître les consonnes et les 4 exceptions clés (shi, chi, tsu, fu)\n"
                    "- Lire le tableau Gojuon (50 sons)\n"
                    "- Comprendre le rythme syllabique (division en mores)\n"
                    "- Distinguer des sons proches à l'oreille"
                ),
                'prerequisites': "Aucun. Ce cours est fait pour les **débutants absolus**.",
                'meta_description': (
                    "Apprenez la prononciation japonaise : voyelles, consonnes, tableau Gojuon "
                    "et rythme syllabique. Cours débutant avec exercices audio."
                ),
                'keywords': "japonais, prononciation, gojuon, voyelles, hiragana, débutant, apprendre japonais",
                'price': 0,
                'is_published': True,
            }
        )
        action = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(f"✅ Cours {action} : {course.title}"))

        # ─── MODULE ───────────────────────────────────────────
        module, _ = Module.objects.update_or_create(
            course=course,
            order=1,
            defaults={'title': "La prononciation japonaise"}
        )
        self.stdout.write(f"   📦 Module : {module.title}")

        # ─── LEÇONS + BLOCS ──────────────────────────────────
        self._create_lesson_1_intro(module)
        self._create_lesson_2_voyelles(module)
        self._create_lesson_3_consonnes(module)
        self._create_lesson_4_gojuon(module)
        self._create_lesson_5_rythme(module)
        self._create_lesson_6_quiz(module)
        self._create_lesson_7_resume(module)

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Cours seedé avec succès ! "
            f"7 leçons, {ContentBlock.objects.filter(lesson__module=module).count()} blocs, "
            f"{QuizQuestion.objects.filter(block__lesson__module=module).count()} questions de quiz."
        ))

    # ───────────────────────────────────────────────────────
    # HELPERS
    # ───────────────────────────────────────────────────────

    def _get_or_create_lesson(self, module, order, title, is_free=False):
        slug = slugify(title)
        lesson, _ = Lesson.objects.update_or_create(
            module=module,
            slug=slug,
            defaults={'title': title, 'order': order, 'is_free': is_free}
        )
        # Nettoyer les anciens blocs pour pouvoir re-run sans doublons
        lesson.blocks.all().delete()
        self.stdout.write(f"   📖 Leçon {order} : {title}")
        return lesson

    def _add_text(self, lesson, order, title, content):
        return ContentBlock.objects.create(
            lesson=lesson, type='text', order=order,
            title=title, text_content=content
        )

    def _add_video(self, lesson, order, title, video_id='PLACEHOLDER'):
        return ContentBlock.objects.create(
            lesson=lesson, type='video', order=order,
            title=title, video_id=video_id
        )

    def _add_audio(self, lesson, order, title, description=''):
        """Crée un bloc audio (sans fichier — à uploader via le builder)."""
        return ContentBlock.objects.create(
            lesson=lesson, type='audio', order=order,
            title=title, text_content=description
        )

    def _add_file(self, lesson, order, title):
        """Crée un bloc fichier (sans fichier — à uploader via le builder)."""
        return ContentBlock.objects.create(
            lesson=lesson, type='file', order=order,
            title=title
        )

    def _add_quiz(self, lesson, order, quiz_title, questions):
        """
        questions = [
            {'text': '...', 'a': '...', 'b': '...', 'c': '...', 'd': None,
             'correct': 'a', 'explanation': '...', 'duration': 15},
        ]
        """
        block = ContentBlock.objects.create(
            lesson=lesson, type='quiz', order=order,
            quiz_title=quiz_title
        )
        for i, q in enumerate(questions, 1):
            QuizQuestion.objects.create(
                block=block,
                order=i,
                question_text=q['text'],
                choice_a=q['a'],
                choice_b=q['b'],
                choice_c=q.get('c') or '',
                choice_d=q.get('d') or '',
                correct_answer=q['correct'],
                explanation=q.get('explanation', ''),
                duration=q.get('duration', 20),
            )
        return block

    # ───────────────────────────────────────────────────────
    # LEÇONS
    # ───────────────────────────────────────────────────────

    def _create_lesson_1_intro(self, module):
        lesson = self._get_or_create_lesson(module, 1, "Introduction au cours", is_free=True)

        self._add_video(lesson, 1, "Introduction au cours")

        self._add_text(lesson, 2, None, (
            "**Minasan, konnichiwa ! Torii gakkou no nihongo ressun he youkoso !**\n\n"
            "Si tu es là, c'est que tu as pris la super décision d'apprendre le japonais. "
            "Félicitations, tu es exactement au bon endroit !\n\n"
            "Pour maîtriser une langue, on passe toujours par les mêmes étapes : "
            "**l'écouter, la parler, la lire et l'écrire.**\n\n"
            "Mais avant même de tracer ton tout premier caractère, il faut qu'on pose des "
            "fondations solides : découvrir comment cette langue sonne et comment elle "
            "fonctionne à l'oral.\n\n"
            "À l'origine, le japonais était une langue 100 % orale, sans le moindre système "
            "d'écriture. Nous allons donc tout naturellement commencer par la base : "
            "**la prononciation.** C'est le programme de ce tout premier cours.\n\n"
            "Installe-toi confortablement, c'est parti !"
        ))

    def _create_lesson_2_voyelles(self, module):
        lesson = self._get_or_create_lesson(module, 2, "Les fondations : Les Voyelles")

        self._add_video(lesson, 1, "Les voyelles")

        self._add_text(lesson, 2, "Les 5 voyelles", (
            "On va commencer par une excellente nouvelle : le japonais est une langue "
            "incroyablement prévisible à prononcer. Tout repose sur **5 voyelles**. "
            "C'est le cœur du réacteur : **a, i, u, e, o**.\n\n"
            "### Guide de prononciation\n\n"
            "| Voyelle | Prononciation |\n"
            "|---------|---------------|\n"
            "| **a** | Comme le « a » en français |\n"
            "| **i** | Comme le « i » en français |\n"
            "| **u** | Entre le « u » et le « eu » — bouche détendue, lèvres non arrondies |\n"
            "| **e** | Toujours prononcé « é » (fermé), jamais comme le « e » muet |\n"
            "| **o** | Comme le « o » en français |\n\n"
            "*Petite précision : le « y » n'est pas considéré comme une voyelle en japonais, "
            "c'est une consonne !*"
        ))

        self._add_audio(lesson, 3,
            "Écoute : Les 5 voyelles (a, i, u, e, o)",
            "Écoute attentivement la prononciation de chaque voyelle."
        )

    def _create_lesson_3_consonnes(self, module):
        lesson = self._get_or_create_lesson(module, 3, "Les Consonnes et les exceptions")

        self._add_video(lesson, 1, "Le mystère des lettres disparues")

        self._add_text(lesson, 2, "Les lettres disparues", (
            "Le japonais n'utilise pas toutes les lettres de l'alphabet latin. "
            "Certaines ont carrément disparu !\n\n"
            "### ⚠️ Lettres absentes\n\n"
            "- Le **« l »** n'existe pas : il est remplacé par un **« r »** très léger "
            "(un peu roulé, comme en espagnol ou en arabe, mais plus doux).\n"
            "  - *Exemple : « London » devient « Rondon »*\n\n"
            "- Le **« v »** n'existe pas non plus dans les lettres de base : "
            "il est remplacé par un **« b »**.\n"
            "  - *Exemple : « Video » devient « Bideo »*\n\n"
            "### Consonnes utilisées\n\n"
            "Pour le reste, tu seras en terrain connu : "
            "**k, g, j, ch, sh, n, m, h, b, p, r, w, y, s, z**."
        ))

    def _create_lesson_4_gojuon(self, module):
        lesson = self._get_or_create_lesson(module, 4, "Le tableau des 50 sons (Gojuon)")

        self._add_video(lesson, 1, "Le tableau magique")

        self._add_text(lesson, 2, "Le Gojuon", (
            "Voici la pièce maîtresse du japonais : le **Gojuon** (le tableau des "
            "cinquante sons). Le principe est simple : on prend une consonne, "
            "on lui colle une voyelle, et ça fait une syllabe.\n\n"
            "| | **a** | **i** | **u** | **e** | **o** |\n"
            "|---|---|---|---|---|---|\n"
            "| — | a | i | u | e | o |\n"
            "| **K** | ka | ki | ku | ke | ko |\n"
            "| **S** | sa | **shi** | su | se | so |\n"
            "| **T** | ta | **chi** | **tsu** | te | to |\n"
            "| **N** | na | ni | nu | ne | no |\n"
            "| **H** | ha | hi | **fu** | he | ho |\n"
            "| **M** | ma | mi | mu | me | mo |\n"
            "| **Y** | ya | *(yi)* | yu | *(ye)* | yo |\n"
            "| **R** | ra | ri | ru | re | ro |\n"
            "| **W** | wa | *(wi)* | *(wu)* | *(we)* | **wo** |\n"
            "| **N** | **n** | | | | |\n\n"
        ))

        self._add_text(lesson, 3, "Les 4 exceptions", (
            "Certains sons décident de faire bande à part et mutent :\n\n"
            "- **t + i** → donne **« chi »** (se prononce *tch*)\n"
            "- **t + u** → donne **« tsu »** (comme *tsunami*)\n"
            "- **s + i** → donne **« shi »** (se prononce *chi*)\n"
            "- **h + u** → donne **« fu »** (un *f* très léger soufflé entre les lèvres)\n\n"
            "### Le « N » solitaire\n\n"
            "Le **« n »** est la **seule consonne** qui a le droit d'exister toute seule, "
            "sans voyelle accrochée à elle ! Elle sonne de manière assez nasale. "
            "Aucun mot ne commence par elle — ça aurait été bien pratique pour écrire "
            "des noms comme « N'golo Kanté » !"
        ))

        self._add_audio(lesson, 4,
            "Écoute : Le Gojuon et les exceptions",
            "Écoute la lecture complète du tableau des 50 sons."
        )

    def _create_lesson_5_rythme(self, module):
        lesson = self._get_or_create_lesson(module, 5, "Le rythme de la langue")

        self._add_video(lesson, 1, "Le rythme dans la peau")

        self._add_text(lesson, 2, "Division syllabique", (
            "Les mots se découpent de manière stricte, comme des blocs Lego. "
            "La règle d'or : **chaque syllabe (ou « more ») compte pour un temps égal "
            "à l'oral.**\n\n"
            "### Exemples\n\n"
            "| Mot | Découpage | Temps |\n"
            "|-----|-----------|-------|\n"
            "| **Nihon** (Japon) | ni - ho - n | 3 temps |\n"
            "| **Kamera** (Caméra) | ka - me - ra | 3 temps |\n"
            "| **Bijutsukan** (Musée d'art) | bi - ju - tsu - ka - n | 5 temps |\n\n"
            "*Le « n » final compte toujours pour un temps à part entière !*"
        ))

    def _create_lesson_6_quiz(self, module):
        lesson = self._get_or_create_lesson(module, 6, "Entraîne ton oreille !")

        self._add_text(lesson, 1, None, (
            "C'est l'heure de tester ton oreille ! Lance les audios et choisis "
            "la bonne réponse. Le but est d'habituer ton cerveau aux nuances du japonais."
        ))

        self._add_audio(lesson, 2,
            "Audio : Quiz des sons",
            "Écoute les 5 sons suivants puis réponds aux questions du quiz ci-dessous."
        )

        self._add_quiz(lesson, 3, "Quiz 1 : Quel son entends-tu ?", [
            {
                'text': "Quel son entends-tu ? (Son n°1)",
                'a': 'ka', 'b': 'ga', 'c': None, 'd': None,
                'correct': 'a',
                'explanation': "Le son « ka » est sourd (sans vibration), contrairement à « ga » qui est sonore.",
                'duration': 15,
            },
            {
                'text': "Quel son entends-tu ? (Son n°2)",
                'a': 'shi', 'b': 'chi', 'c': 'ri', 'd': None,
                'correct': 'b',
                'explanation': "« chi » se prononce comme « tchi ». « shi » serait plus sifflant.",
                'duration': 15,
            },
            {
                'text': "Quel son entends-tu ? (Son n°3)",
                'a': 'tsu', 'b': 'su', 'c': 'u', 'd': None,
                'correct': 'a',
                'explanation': "« tsu » commence par un « t » suivi du « su ». Comme dans tsunami !",
                'duration': 15,
            },
            {
                'text': "Quel son entends-tu ? (Son n°4)",
                'a': 'kyu', 'b': 'kyuu', 'c': 'gyu', 'd': None,
                'correct': 'b',
                'explanation': "La voyelle longue « kyuu » dure deux temps, contrairement à « kyu » (un temps).",
                'duration': 15,
            },
            {
                'text': "Quel son entends-tu ? (Son n°5)",
                'a': 'mu', 'b': 'nu', 'c': 'fu', 'd': None,
                'correct': 'c',
                'explanation': "« fu » est un souffle léger entre les lèvres, très différent de « mu » et « nu ».",
                'duration': 15,
            },
        ])

        self._add_audio(lesson, 4,
            "Audio : Quiz des mots",
            "En japonais, une simple consonne change tout le sens du mot ! Écoute les 5 mots."
        )

        self._add_quiz(lesson, 5, "Quiz 2 : Quel mot entends-tu ?", [
            {
                'text': "Quel mot entends-tu ? (Mot n°1)",
                'a': 'kagi (clé)', 'b': 'kaki (kaki)', 'c': None, 'd': None,
                'correct': 'a',
                'explanation': "« kagi » contient le son sonore « g », tandis que « kaki » a un « k » sourd.",
                'duration': 15,
            },
            {
                'text': "Quel mot entends-tu ? (Mot n°2)",
                'a': 'ashi (pied)', 'b': 'aji (goût)', 'c': None, 'd': None,
                'correct': 'b',
                'explanation': "« aji » utilise le son « j » (sonore), alors que « ashi » utilise « sh » (sourd).",
                'duration': 15,
            },
            {
                'text': "Quel mot entends-tu ? (Mot n°3)",
                'a': 'ishi (pierre)', 'b': 'ichi (un)', 'c': None, 'd': None,
                'correct': 'a',
                'explanation': "« ishi » a le son « sh » sifflant, « ichi » a le son « ch » (tch).",
                'duration': 15,
            },
            {
                'text': "Quel mot entends-tu ? (Mot n°4)",
                'a': 'tenki (météo)', 'b': 'denki (électricité)', 'c': None, 'd': None,
                'correct': 'b',
                'explanation': "« denki » commence par « d » (sonore), « tenki » par « t » (sourd).",
                'duration': 15,
            },
            {
                'text': "Quel mot entends-tu ? (Mot n°5)",
                'a': 'hibi (jours)', 'b': 'hebi (serpent)', 'c': None, 'd': None,
                'correct': 'b',
                'explanation': "La différence est dans la voyelle : « hebi » (he = é), « hibi » (hi = i).",
                'duration': 15,
            },
        ])

    def _create_lesson_7_resume(self, module):
        lesson = self._get_or_create_lesson(module, 7, "Ce qu'il faut retenir")

        self._add_text(lesson, 1, "Résumé du cours", (
            "### Les points essentiels\n\n"
            "- Le japonais s'appuie sur **5 voyelles** : a, i, u, e, o\n"
            "- Le **« n »** est la seule consonne qui s'écrit seule\n"
            "- Les lettres **L** et **V** n'existent pas (remplacées par R et B)\n"
            "- Attention aux **4 exceptions** du tableau : **shi, chi, tsu, fu**\n"
            "- Chaque syllabe compte pour **un temps égal**\n\n"
            "N'oublie pas de télécharger la fiche d'exercices ci-dessous pour t'entraîner. "
            "Dans le prochain cours, on passera aux choses sérieuses : "
            "**tes premiers caractères japonais !** Mata ne !"
        ))

        self._add_file(lesson, 2, "Fiche d'exercices — Prononciation")
