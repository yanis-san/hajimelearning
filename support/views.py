from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from courses.models import Lesson
from .forms import QuestionForm,ResponseForm
from .models import Question,Response
from django.conf import settings

@login_required
def ask_question(request, lesson_id):
    """ Traite le formulaire envoyé depuis une leçon """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.student = request.user
            question.course = course
            question.lesson = lesson
            question.save()
            
            messages.success(request, "Votre question a été envoyée ! Un instructeur vous répondra bientôt.")
            # On retourne sur la leçon
            return redirect('lesson_detail', course_slug=course.slug, lesson_slug=lesson.slug)
    
    # Si on essaie d'accéder à cette URL sans POST, on renvoie à la leçon
    return redirect('lesson_detail', course_slug=course.slug, lesson_slug=lesson.slug)


@login_required
def question_detail(request, question_id):
    """ Page de discussion : Question + Réponses """
    question = get_object_or_404(Question, id=question_id)
    
    # Gestion de la réponse
    if request.method == 'POST':
        # VÉRIFICATION DES PERMISSIONS
        is_author = request.user == question.student
        is_staff = request.user.is_staff
        allow_others = getattr(settings, 'ALLOW_STUDENT_REPLIES', False)

        if is_author or is_staff or allow_others:
            form = ResponseForm(request.POST)
            if form.is_valid():
                response = form.save(commit=False)
                response.question = question
                response.author = request.user
                response.is_instructor = is_staff # Marque si c'est une réponse officielle
                response.save()
                
                # Si c'est l'étudiant qui répond, on peut remettre en OPEN si c'était RESOLVED
                if is_author and question.status == 'RESOLVED':
                    question.status = 'OPEN'
                    question.save()
                    
                messages.success(request, "Réponse publiée.")
                return redirect('question_detail', question_id=question.id)
        else:
            messages.error(request, "Les réponses sont désactivées pour les autres étudiants.")

    else:
        form = ResponseForm()

    return render(request, 'support/question_detail.html', {
        'question': question,
        'form': form,
        'can_reply': (request.user == question.student) or request.user.is_staff or getattr(settings, 'ALLOW_STUDENT_REPLIES', False)
    })

@login_required
def my_questions(request):
    """ Dashboard Support : Liste des questions """
    user_questions = Question.objects.filter(student=request.user).order_by('-updated_at')
    
    # On sépare en deux listes pour les onglets
    pending = user_questions.exclude(status='RESOLVED')
    resolved = user_questions.filter(status='RESOLVED')

    return render(request, 'support/my_questions.html', {
        'pending': pending,
        'resolved': resolved
    })

@login_required
def mark_resolved(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    # Sécurité : Seul l'auteur ou le staff peut fermer
    if request.user == question.student or request.user.is_staff:
        if question.status != 'RESOLVED':
            question.status = 'RESOLVED'
            question.save()
            messages.success(request, "La discussion a été marquée comme résolue.")
    else:
        messages.error(request, "Vous n'avez pas la permission de fermer ce ticket.")
    
    return redirect('question_detail', question_id=question.id)