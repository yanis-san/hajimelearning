from django.urls import path
from . import views

urlpatterns = [
    path('', views.instructor_plans, name='instructor_plans'),
    path('request/<slug:plan_slug>/', views.instructor_request, name='instructor_request'),
    path('pending/', views.instructor_request_pending, name='instructor_request_pending'),
    path('dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('courses/create/', views.instructor_course_create, name='instructor_course_create'),
    path('courses/<slug:course_slug>/edit/', views.instructor_course_edit, name='instructor_course_edit'),
]
