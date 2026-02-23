from django.urls import path
from . import views

urlpatterns = [
    # Page qui liste toutes les notifications
    path('', views.my_notifications, name='my_notifications'),
    
    # Action "Classique" (Clic -> Marque lu -> Redirige vers la page cible)
    # Utile pour les liens dans les emails ou si JS est désactivé
    path('read/<int:notification_id>/', views.mark_read_and_redirect, name='mark_read_and_redirect'),
    
    # Action "HTMX" (Clic -> Marque lu -> Met à jour le style et le badge sans recharger)
    # C'est celle utilisée par le dropdown Alpine.js
    path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notif_read'),
    
    # Action "Tout marquer comme lu"
    path('mark-all/', views.mark_all_read, name='mark_all_read'),
]