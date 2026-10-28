import re

from django import forms
from django.utils.text import slugify

from .models import ContentBlock, Course, LandingSection, Lesson, Module, QuizQuestion


# Formulaire du Bloc (Parent)
class ContentBlockForm(forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = ['title', 'text_content', 'video_id', 'file_content', 'related_file', 'quiz_title']

    def clean_title(self):
        return self.cleaned_data.get('title') or None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Styling Tailwind
        for field in self.fields:
            self.fields[field].widget.attrs.update(
                {
                    'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent transition'
                }
            )
        self.fields['title'].widget.attrs.update({'placeholder': 'Titre du bloc'})
        self.fields['text_content'].widget.attrs.update(
            {
                'rows': 12,
                'placeholder': 'Votre texte (Markdown)...',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent transition font-mono text-sm resize-y',
            }
        )
        self.fields['video_id'].widget.attrs.update({'placeholder': 'Ex: dQw4w9WgXcQ'})
        self.fields['quiz_title'].widget.attrs.update({'placeholder': 'Ex: Test de connaissances'})
        self.fields['file_content'].widget.attrs.update(
            {
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/5 file:text-primary-dark hover:file:bg-primary/10'
            }
        )


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = [
            'question_text',
            'duration',
            'choice_a',
            'choice_b',
            'choice_c',
            'choice_d',
            'correct_answer',
            'explanation',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'w-full p-2 border border-gray-300 rounded mb-2 text-sm'})
        # Petit style pour le temps
        self.fields['duration'].widget.attrs.update({'placeholder': 'Ex: 15'})


# ── Formulaires Admin CRUD ──────────────────────────

TAILWIND_INPUT = (
    'w-full px-4 py-2.5 border-2 border-gray-300 rounded-xl bg-stone-50/80 text-gray-900 '
    'placeholder-gray-400 focus:bg-white focus:outline-none focus:border-gray-900 '
    'focus:ring-2 focus:ring-gray-900/10 transition-all text-sm font-medium shadow-2xs hover:border-gray-400'
)
TAILWIND_TEXTAREA = (
    'w-full px-4 py-3 border-2 border-gray-300 rounded-xl bg-stone-50/80 text-gray-900 '
    'placeholder-gray-400 focus:bg-white focus:outline-none focus:border-gray-900 '
    'focus:ring-2 focus:ring-gray-900/10 transition-all text-sm resize-y shadow-2xs hover:border-gray-400'
)
TAILWIND_CHECKBOX = (
    'w-5 h-5 rounded-md border-2 border-gray-300 text-gray-900 focus:ring-gray-900/20 transition cursor-pointer'
)
TAILWIND_FILE = (
    'block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-2 '
    'file:border-gray-900 file:text-xs file:font-bold file:bg-yellow-300 file:text-gray-950 '
    'hover:file:bg-yellow-400 file:cursor-pointer file:transition file:shadow-xs'
)


class CourseForm(forms.ModelForm):
    MONO = 'font-mono text-sm leading-relaxed'
    FIELD_ATTRS = {
        'title': {'class': 'font-bold text-base', 'placeholder': 'Ex: Japonais Débutant - JLPT N5'},
        'slug': {'class': 'font-mono text-sm', 'placeholder': 'japonais-n5'},
        'price': {'class': 'font-bold text-base', 'placeholder': '0'},
        'short_description': {
            'rows': 3,
            'placeholder': "Courte phrase d'accroche (visible sur la carte du cours en page d'accueil)...",
        },
        'description': {
            'class': MONO,
            'rows': 12,
            'placeholder': 'Description complète et détaillée de la formation (Markdown supporté)...',
        },
        'what_you_will_learn': {
            'class': MONO,
            'rows': 6,
            'placeholder': '- Première compétence ou acquis\n- Deuxième compétence\n- Troisième point fort...',
        },
        'prerequisites': {
            'class': MONO,
            'rows': 4,
            'placeholder': 'Ex: Aucun prérequis, idéal pour débutant complet.',
        },
        'trailer_video_id': {'class': 'font-mono text-sm', 'placeholder': 'Ex: dQw4w9WgXcQ (ID YouTube ou lien)'},
        'meta_description': {
            'rows': 3,
            'maxlength': '160',
            'placeholder': 'Résumé percutant pour Google et les moteurs de recherche (max 160 caractères)...',
        },
        'keywords': {'placeholder': 'japonais, n5, jlpt, vocabulaire, kanji, cours'},
    }

    class Meta:
        model = Course
        fields = [
            'title',
            'slug',
            'short_description',
            'description',
            'what_you_will_learn',
            'prerequisites',
            'trailer_video_id',
            'meta_description',
            'keywords',
            'price',
            'thumbnail',
            'cover_image',
            'is_published',
            'is_featured',
            'hide_title_on_card',
        ]
        widgets = {
            'description': forms.Textarea(),
            'what_you_will_learn': forms.Textarea(),
            'prerequisites': forms.Textarea(),
            'short_description': forms.Textarea(),
            'meta_description': forms.Textarea(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['slug'].help_text = 'URL du cours. Généré automatiquement si vide.'

        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = TAILWIND_CHECKBOX
            elif isinstance(widget, forms.FileInput):
                widget.attrs['class'] = TAILWIND_FILE
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update(
                    {
                        'class': TAILWIND_TEXTAREA,
                        'rows': 6,
                    }
                )
            else:
                widget.attrs['class'] = TAILWIND_INPUT

        # Personnalisations par champ (classes additionnelles, lignes, placeholder)
        for name, attrs in self.FIELD_ATTRS.items():
            if name in self.fields:
                widget = self.fields[name].widget
                attrs = dict(attrs)
                extra_class = attrs.pop('class', '')
                widget.attrs.update(attrs)
                if extra_class:
                    widget.attrs['class'] = f"{widget.attrs['class']} {extra_class}"

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            slug = slugify(self.cleaned_data.get('title', ''))
        return slug

    def clean_trailer_video_id(self):
        val = self.cleaned_data.get('trailer_video_id', '')
        if val:
            val = val.strip()
            m = re.search(r'(?:v=|\/|youtu\.be\/)([a-zA-Z0-9_-]{11})', val)
            if m:
                return m.group(1)
        return val


class InstructorCourseForm(CourseForm):
    """Formulaire cours pour instructeurs : pas de mise en avant ni d'options admin."""

    class Meta(CourseForm.Meta):
        fields = [
            'title',
            'slug',
            'short_description',
            'description',
            'what_you_will_learn',
            'prerequisites',
            'trailer_video_id',
            'meta_description',
            'keywords',
            'price',
            'thumbnail',
            'cover_image',
            'is_published',
        ]
        widgets = {
            'description': forms.Textarea(),
            'what_you_will_learn': forms.Textarea(),
            'prerequisites': forms.Textarea(),
            'short_description': forms.Textarea(),
            'meta_description': forms.Textarea(),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update(
            {
                'class': TAILWIND_INPUT,
                'placeholder': 'Nom du module',
            }
        )


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'slug', 'is_free']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update(
            {
                'class': TAILWIND_INPUT,
                'placeholder': 'Titre de la leçon',
            }
        )
        self.fields['slug'].widget.attrs.update(
            {
                'class': TAILWIND_INPUT,
                'placeholder': 'slug-de-la-lecon',
            }
        )
        self.fields['slug'].required = False
        self.fields['slug'].help_text = 'Généré automatiquement si vide.'
        self.fields['is_free'].widget.attrs['class'] = TAILWIND_CHECKBOX

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            slug = slugify(self.cleaned_data.get('title', ''))
        return slug


class LandingSectionForm(forms.ModelForm):
    class Meta:
        model = LandingSection
        fields = [
            'title',
            'body',
            'image',
            'video_id',
            'subtitle',
            'cta_text',
            'cta_url',
            'image_position',
            'css_class',
            'background',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.FileInput):
                widget.attrs['class'] = TAILWIND_FILE
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({'class': TAILWIND_TEXTAREA, 'rows': 8})
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = TAILWIND_INPUT
            else:
                widget.attrs['class'] = TAILWIND_INPUT

        self.fields['title'].widget.attrs['placeholder'] = 'Titre de la section (optionnel)'
        self.fields['video_id'].widget.attrs['placeholder'] = 'Ex: dQw4w9WgXcQ'
        self.fields['css_class'].widget.attrs['placeholder'] = 'Ex: py-12 text-center'
        self.fields['subtitle'].widget.attrs['placeholder'] = 'Sous-titre ou accroche courte'
        self.fields['cta_text'].widget.attrs['placeholder'] = 'Ex: S\'inscrire maintenant'
        self.fields['cta_url'].widget.attrs['placeholder'] = 'Ex: #inscription ou https://...'
        self.fields['image_position'].required = False
        self.fields['body'].widget.attrs.update(
            {
                'rows': 10,
                'placeholder': 'Contenu Markdown…',
                'class': TAILWIND_TEXTAREA + ' font-mono text-sm',
            }
        )
