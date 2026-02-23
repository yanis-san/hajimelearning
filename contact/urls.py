from django.urls import path
from . import views

urlpatterns = [
    path('', views.ContactView.as_view(), name='contact'),
    path('merci/', views.ContactSuccessView.as_view(), name='contact_success'),
]
