from django.urls import path
from . import views

urlpatterns = [
    path('ask/<int:lesson_id>/', views.ask_question, name='ask_question'),
    path('discussion/<int:question_id>/', views.question_detail, name='question_detail'),
    path('my-questions/', views.my_questions, name='my_questions'),
    path('resolve/<int:question_id>/', views.mark_resolved, name='mark_resolved'),
    path('course/<slug:course_slug>/', views.instructor_course_questions, name='instructor_course_questions'),
]