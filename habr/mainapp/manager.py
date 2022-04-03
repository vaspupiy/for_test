from django.db import models
from django.db.models import Q


class ArticleManager(models.Manager):
    use_for_related_fields = True

    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            or_lookup = (Q(title__iregex=query) | Q(subtitle__iregex=query) | Q(text__iregex=query))
            qs = qs.filter(or_lookup)

        return qs
