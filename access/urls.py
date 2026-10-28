from django.urls import path

from . import views

urlpatterns = [
    path('request/<int:course_id>/', views.request_course_access, name='request_access'),
    path('enroll/<int:course_id>/', views.enroll_free_course, name='enroll_free'),
    path('validate-coupon/<int:course_id>/', views.validate_coupon, name='validate_coupon'),
    path('receipt/<int:request_id>/', views.download_receipt, name='download_receipt'),
]
