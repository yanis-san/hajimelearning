from django.urls import path
from access.views import request_course_access, validate_coupon
from . import views

urlpatterns = [
    path('request/<int:course_id>/', request_course_access, name='request_access'),
    path('validate-coupon/<int:course_id>/', validate_coupon, name='validate_coupon'),
    path('receipt/<int:request_id>/', views.download_receipt, name='download_receipt'),
]

