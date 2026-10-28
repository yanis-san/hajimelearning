from django.contrib.sitemaps import Sitemap

from .models import Course


class CourseSitemap(Sitemap):
    changefreq = "weekly" # Google repassera chaque semaine
    priority = 0.8        # Importance (0.0 à 1.0)

    def items(self):
        # On n'indexe QUE les cours publiés
        # ET on les trie par date de modification pour éviter le warning de pagination
        return Course.objects.filter(is_published=True).order_by('-created_at')

    def lastmod(self, obj):
        # Indique à Google la date de dernière mise à jour du contenu
        return obj.updated_at