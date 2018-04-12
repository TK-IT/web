from constance.test import override_config
from datetime import date
from django.test import TestCase
from freezegun import freeze_time
from tkweb.apps.eval.models import WikiArticleTimeout
from wiki.models import Article


@freeze_time("2018-09-20")
@override_config(GFYEAR="2017")
class WikiArticleTimeoutTestOutdatedRightBeforeGF(TestCase):

    def setUp(self):
        Article.objects.create()

    def test_none_both(self):
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = None
        instance.updated = None
        self.assertIsNone(instance.outdated())

    def test_none_updated(self):
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 1
        instance.updated = None
        self.assertIsNotNone(instance.outdated())
        self.assertTrue(instance.outdated())

    def test_none_timeout(self):
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = None
        instance.updated = date(2018, 1, 1)
        self.assertIsNotNone(instance.outdated())
        self.assertFalse(instance.outdated())

    def test_clearly_outdated(self):
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 1
        instance.updated = date(2010, 1, 1)
        self.assertTrue(instance.outdated())

    def test_updated(self):
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 1
        instance.updated = date(2018, 9, 5)
        self.assertIsNotNone(instance.outdated())
        self.assertFalse(instance.outdated())

    def test_open_outdated(self):
        """
        TK-Open 2018. Ikke opdateret siden året før.
        """
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 9
        instance.updated = date(2017, 10, 1)
        self.assertTrue(instance.outdated())

    def test_open_updated(self):
        """
        TK-Open 2018. Lige opdateret.
        """
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 9
        instance.updated = date(2018, 9, 19)
        self.assertIsNotNone(instance.outdated())
        self.assertFalse(instance.outdated())

    def test_jul_outdated(self):
        """
        Julefest 2017. Eval ikke skrevet endnu.
        """
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 12
        instance.updated = date(2017, 1, 1)
        self.assertTrue(instance.outdated())

    def test_jul_updated(self):
        """
        Julefest 2017. Eval skrevet lige efter.
        """
        instance = WikiArticleTimeout.objects.all()[0]
        instance.timeoutMonth = 12
        instance.updated = date(2018, 1, 1)
        self.assertIsNotNone(instance.outdated())
        self.assertFalse(instance.outdated())
