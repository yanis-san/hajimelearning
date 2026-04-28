from django.urls import path
from django.conf import settings
from . import views
from django.contrib import admin
from django.urls import path, include
# --- AJOUTE CETTE LIGNE ---
from django.conf import settings 
# --------------------------
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    # Page d'accueil (Liste des cours)
    path('', views.course_list, name='course_list'),
    # Page catalogue dédiée
    path('catalogue/', views.catalogue, name='catalogue'),
    
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    # Page d'un cours (ex: /course/python-debutant/)
    path('course/<slug:course_slug>/', views.course_detail, name='course_detail'),
    
    # Page d'une leçon (ex: /course/python-debutant/lesson/installation/)
    path('course/<slug:course_slug>/lesson/<slug:lesson_slug>/', views.lesson_detail, name='lesson_detail'),
    path('course/<slug:course_slug>/lesson/<slug:lesson_slug>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('course/<slug:course_slug>/certificate/', views.download_certificate, name='download_certificate'),

    # ── Admin CRUD ──
    path('manage/courses/', views.manage_course_list, name='manage_course_list'),
    path('manage/courses/create/', views.manage_course_create, name='manage_course_create'),
    path('manage/courses/<slug:course_slug>/edit/', views.manage_course_edit, name='manage_course_edit'),
    path('manage/courses/<slug:course_slug>/delete/', views.manage_course_delete, name='manage_course_delete'),
    path('manage/courses/<slug:course_slug>/modules/', views.manage_course_modules, name='manage_course_modules'),
    path('manage/courses/<slug:course_slug>/modules/<int:module_id>/edit/', views.manage_module_edit, name='manage_module_edit'),
    path('manage/courses/<slug:course_slug>/modules/<int:module_id>/delete/', views.manage_module_delete, name='manage_module_delete'),
    path('manage/courses/<slug:course_slug>/modules/reorder/', views.manage_module_reorder, name='manage_module_reorder'),

    # ── Landing page builder ──
    path('manage/courses/<slug:course_slug>/landing/', views.manage_course_landing, name='manage_course_landing'),
    path('manage/courses/<slug:course_slug>/landing/add/<str:section_type>/', views.add_landing_section, name='add_landing_section'),
    path('manage/courses/<slug:course_slug>/landing/reorder/', views.reorder_landing_sections, name='reorder_landing_sections'),
    path('manage/landing/edit/<int:section_id>/', views.edit_landing_section, name='edit_landing_section'),
    path('manage/landing/delete/<int:section_id>/', views.delete_landing_section, name='delete_landing_section'),
    path('manage/landing/duplicate/<int:section_id>/', views.duplicate_landing_section, name='duplicate_landing_section'),
    path('manage/landing/toggle/<int:section_id>/', views.toggle_landing_section_visibility, name='toggle_landing_section_visibility'),
    path('manage/courses/<slug:course_slug>/landing/prefill/', views.prefill_landing_template, name='prefill_landing_template'),

    path('manage/courses/<slug:course_slug>/modules/<int:module_id>/lessons/', views.manage_module_lessons, name='manage_module_lessons'),
    path('manage/courses/<slug:course_slug>/modules/<int:module_id>/lessons/<int:lesson_id>/edit/', views.manage_lesson_edit, name='manage_lesson_edit'),
    path('manage/courses/<slug:course_slug>/modules/<int:module_id>/lessons/<int:lesson_id>/delete/', views.manage_lesson_delete, name='manage_lesson_delete'),
    path('manage/courses/<slug:course_slug>/modules/<int:module_id>/lessons/reorder/', views.manage_lesson_reorder, name='manage_lesson_reorder'),

    # ── Builder existant ──
    path('manage/course/<slug:course_slug>/lesson/<slug:lesson_slug>/', views.manage_lesson_content, name='manage_lesson_content'),
    
    path('manage/block/add/<int:lesson_id>/<str:block_type>/', views.add_block, name='add_block'),
    path('manage/block/edit/<int:block_id>/', views.edit_block, name='edit_block'),
    path('manage/block/delete/<int:block_id>/', views.delete_block, name='delete_block'),
    path('manage/block/order/<int:block_id>/<str:direction>/', views.order_block, name='order_block'),
    path('manage/block/reorder/', views.update_block_order, name='update_block_order'),
    path('manage/quiz/add-question/<int:block_id>/', views.add_quiz_question, name='add_quiz_question'),
    path('manage/quiz/delete-question/<int:question_id>/', views.delete_quiz_question, name='delete_quiz_question'),
    path('api/save-quiz/<int:block_id>/', views.save_quiz_result, name='save_quiz_result'),
    path('manage/course/<slug:course_slug>/stats/', views.manage_course_students, name='manage_course_students'),
    path('manage/preview-markdown/', views.preview_markdown, name='preview_markdown'),
]



if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
else:
    # En développement local
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)