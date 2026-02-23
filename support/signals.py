# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.urls import reverse
# from .models import Response
# from notifications.models import Notification

# @receiver(post_save, sender=Response)
# def notify_student_on_reply(sender, instance, created, **kwargs):
#     if created:
#         question = instance.question
#         # On notifie l'auteur de la question SEULEMENT si ce n'est pas lui qui répond
#         if instance.author != question.student:
#             Notification.objects.create(
#                 recipient=question.student,
#                 message=f"Nouvelle réponse sur : {question.title}",
#                 link=reverse('question_detail', args=[question.id])
#             )