from django.db import models
from django.conf import settings
from courses.models import Course, Lesson

class Question(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'En attente'),
        ('RESOLVED', 'Résolu'),
        ('CLOSED', 'Fermé'),
    )

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, help_text="La leçon concernée (optionnel)")
    
    title = models.CharField("Sujet", max_length=200)
    content = models.TextField("Votre question")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.student.email})"

class Response(models.Model):
    """ Une réponse (de l'admin ou de l'élève) """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField("Réponse")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Pour savoir si c'est une réponse officielle (Prof/Admin)
    is_instructor = models.BooleanField(default=False)

    def __str__(self):
        return f"Rep: {self.question.title} par {self.author}"