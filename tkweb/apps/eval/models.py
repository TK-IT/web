from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import dateparse
from tkweb.apps.eval.evalmacros import (
    parseTimeoutMonth, EvalMacroPattern,
)
from wiki.models import Article
import datetime
import re


class WikiArticleTimeout(models.Model):
    article = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        related_name="wikiArticleTimeout")
    timeoutMonth = models.PositiveSmallIntegerField(null=True)
    updated = models.DateField(null=True)
    title = models.CharField(max_length=300)

    def __str__(self):
        return '%s: %s' % (self.article, self.timeoutMonth)

    def timeout(self):
        if self.timeoutMonth:
            year = datetime.date.today().year
            if self.timeoutMonth > 9:
                year -= 1

            return datetime.date(
                year=year,
                month=self.timeoutMonth,
                day=1)
        return None

    def outdated(self):
        if self.timeoutMonth and self.updated:
            return self.updated < self.timeout()

        if self.timeoutMonth and self.updated is None:
            return True

        if self.timeoutMonth is None and self.updated:
            return False

        return None


@receiver(post_save, sender=Article)
def wikiArticle_callback(sender, instance, **kwargs):
    timeout = None
    title = ''
    updated = None
    if instance.current_revision is not None:
        lines = instance.current_revision.content

        try:
            match = EvalMacroPattern.find_macro_invocations(
                lines, 'timeout')[0]
            timeout = parseTimeoutMonth(match.args[0])
        except (IndexError, ValueError):
            # No/invalid timeout
            pass

        try:
            match = EvalMacroPattern.find_macro_invocations(
                lines, 'updated')[0]
            title = match.args[0]
            updated = dateparse.parse_date(match.args[1])
        except (IndexError, ValueError):
            # No/invalid updated
            pass

    try:
        wikiArticleTimeout = instance.wikiArticleTimeout
    except WikiArticleTimeout.DoesNotExist:
        wikiArticleTimeout = WikiArticleTimeout(article=instance)

    wikiArticleTimeout.timeoutMonth = timeout
    wikiArticleTimeout.title = title
    wikiArticleTimeout.updated = updated
    wikiArticleTimeout.save()
