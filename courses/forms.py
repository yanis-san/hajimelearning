from django import forms
from django.utils.text import slugify
from .models import Course, Module, Lesson, ContentBlock, QuizQuestion, LandingSection

# Formulaire du Bloc (Parent)
class ContentBlockForm(forms.ModelForm):
    class Meta:
        model = ContentBlock
        fields = ['title','text_content', 'video_id', 'file_content','related_file', 'quiz_title']
    
    def clean_title(self):
        return self.cleaned_data.get('title') or None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Styling Tailwind
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent transition'
            })
        self.fields['title'].widget.attrs.update({'placeholder': 'Titre du bloc'})
        self.fields['text_content'].widget.attrs.update({
            'rows': 12,
            'placeholder': 'Votre texte (Markdown)...',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent transition font-mono text-sm resize-y',
        })
        self.fields['video_id'].widget.attrs.update({'placeholder': 'Ex: dQw4w9WgXcQ'})
        self.fields['quiz_title'].widget.attrs.update({'placeholder': 'Ex: Test de connaissances'})
        self.fields['file_content'].widget.attrs.update({'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100'})

class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ['question_text', 'duration', 'choice_a', 'choice_b', 'choice_c', 'choice_d', 'correct_answer', 'explanation']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full p-2 border border-gray-300 rounded mb-2 text-sm'
            })
        # Petit style pour le temps
        self.fields['duration'].widget.attrs.update({'placeholder': 'Ex: 15'})


# ── Formulaires Admin CRUD ──────────────────────────

TAILWIND_INPUT = 'w-full px-4 py-2.5 border border-gray-300 rounded-xl bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-transparent transition text-sm'
TAILWIND_TEXTAREA = TAILWIND_INPUT + ' resize-y'
TAILWIND_CHECKBOX = 'rounded border-gray-300 text-orange-500 focus:ring-orange-400'
TAILWIND_FILE = 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100'


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'short_description', 'description',
            'what_you_will_learn', 'prerequisites', 'trailer_video_id',
            'meta_description', 'keywords', 'price', 'thumbnail', 'cover_image',
            'is_published', 'is_featured', 'hide_title_on_card',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['slug'].help_text = 'URL du cours. Généré automatiquement si vide.'

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            slug = slugify(self.cleaned_data.get('title', ''))
        return slug


class InstructorCourseForm(CourseForm):
    """Formulaire cours pour instructeurs : pas de mise en avant ni d'options admin."""
    class Meta(CourseForm.Meta):
        fields = [
            'title', 'slug', 'short_description', 'description',
            'what_you_will_learn', 'prerequisites', 'trailer_video_id',
            'meta_description', 'keywords', 'price', 'thumbnail', 'cover_image',
            'is_published',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = TAILWIND_CHECKBOX
            elif isinstance(widget, forms.FileInput):
                widget.attrs['class'] = TAILWIND_FILE
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({
                    'class': TAILWIND_TEXTAREA,
                    'rows': 6,
                })
            else:
                widget.attrs['class'] = TAILWIND_INPUT

        self.fields['description'].widget.attrs['rows'] = 10
        self.fields['short_description'].widget = forms.Textarea(attrs={
            'class': TAILWIND_TEXTAREA, 'rows': 3,
        })


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'class': TAILWIND_INPUT,
            'placeholder': 'Nom du module',
        })


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'slug', 'is_free']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'class': TAILWIND_INPUT,
            'placeholder': 'Titre de la leçon',
        })
        self.fields['slug'].widget.attrs.update({
            'class': TAILWIND_INPUT,
            'placeholder': 'slug-de-la-lecon',
        })
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
        fields = ['title', 'body', 'image', 'video_id', 'subtitle',
                  'cta_text', 'cta_url', 'image_position', 'css_class', 'background']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
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
        self.fields['body'].widget.attrs.update({
            'rows': 10,
            'placeholder': 'Contenu Markdown…',
            'class': TAILWIND_TEXTAREA + ' font-mono text-sm',
        })