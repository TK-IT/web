from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from tkweb.apps.eval.evalmacros import MONTHS, parseTimeoutMonth
from wiki.models import Article
import datetime
import re


class WikiArticleTimeout(models.Model):
    article = models.OneToOneField(
        Article,
        related_name="wikiArticleTimeout")
    timeoutMonth = models.PositiveSmallIntegerField(null=True)
    updated = models.DateField(null=True)

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
        if self.timeoutMonth:
            return self.updated < self.timeout()
        return None


@receiver(post_save, sender=Article)
def wikiArticle_callback(sender, instance, **kwargs):
    if instance.current_revision is not None:
        lines = instance.current_revision.content

        toPattern = (r"\[timeout(?:\s+(?P<month>(%s)))\]" %
                     '|'.join(m for ml in MONTHS for m in ml))
        toMo = re.search(toPattern, lines, re.IGNORECASE)
        if toMo is not None:
            timeout = parseTimeoutMonth(toMo.group('month'))
        else:
            timeout = None

        upPattern = (r"\[updated(?:\s+(?P<title>[^\s\n]{0,300}))" +
                     "(?:\s+(?P<date>\d{4}-\d{1,2}-\d{1,2}))\]")
        upMo = re.search(upPattern, lines, re.IGNORECASE)
        if upMo is not None:
            updated = datetime.datetime.strptime(upMo.group('date'),
                                                 "%Y-%m-%d").date()
        else:
            updated = None
    else:
        timeout = None
        updated = None

    try:
        wikiArticleTimeout = instance.wikiArticleTimeout
    except WikiArticleTimeout.DoesNotExist:
        wikiArticleTimeout = WikiArticleTimeout(article=instance)

    wikiArticleTimeout.timeoutMonth = timeout
    wikiArticleTimeout.updated = updated
    wikiArticleTimeout.save()
