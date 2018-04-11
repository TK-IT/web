from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from tkweb.apps.evalmacros.evalmacros import MONTHS, parseTimeoutMonth
from wiki.models import Article
import re


class WikiArticleTimeout(models.Model):
    article = models.OneToOneField(
        Article,
        related_name="wikiArticleTimeout")
    month = models.PositiveSmallIntegerField()

    def __str__(self):
        return '%s: %s' % (self.article, self.month)


@receiver(post_save, sender=Article)
def wikiArticle_callback(sender, instance, **kwargs):
    lines = instance.current_revision.content

    pattern = (r"\[timeout(?:\s+(?P<month>(%s)))\]" %
               '|'.join(m for ml in MONTHS for m in ml))
    mo = re.search(pattern, lines, re.IGNORECASE)
    if mo is not None:
        month = parseTimeoutMonth(mo.group('month'))
    else:
        month = 0

    try:
        wikiArticleTimeout = instance.wikiArticleTimeout
    except WikiArticleTimeout.DoesNotExist:
        wikiArticleTimeout = WikiArticleTimeout(article=instance)

    wikiArticleTimeout.month = month
    wikiArticleTimeout.save()
