from django import forms

from .models import Question, Response


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['title', 'content']
        labels = {
            'title': 'Sujet de votre question',
            'content': 'Détails'
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': "Ex: Je ne comprends pas la boucle for...", 'class': 'w-full'}),
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': "Posez votre question ici..."}),
        }

class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['content']
        labels = {'content': 'Votre réponse'}
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': "Écrivez votre réponse ici..."}),
        }
