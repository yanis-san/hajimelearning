"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve

from courses.sitemaps import CourseSitemap

# Dictionnaire des sitemaps
sitemaps = {
    'courses': CourseSitemap,
}


urlpatterns = [
    path('admin/', admin.site.urls),
    path('markdownx/', include('markdownx.urls')),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),
    path('access/', include('access.urls')),
    path('support/', include('support.urls')),
    path('contact/', include('contact.urls')),
    path('', include('courses.urls')),
    path('notifications/', include('notifications.urls')),
    path('instructors/', include('instructors.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    # Médias servis par Django : configurer Apache pour le dossier media est complexe sur cPanel mutualisé.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
