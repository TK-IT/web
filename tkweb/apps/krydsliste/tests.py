import unittest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from tkweb.apps.krydsliste.forms import SheetForm
from tkweb.apps.krydsliste.models import Sheet


class NonUtf8ErrorTest(TestCase):
    def setUp(self):
        user = User.objects.create(username="test", is_staff=True, is_superuser=True)
        self.client.force_login(user)

    def test(self):
        sheet = Sheet.objects.create(name="test")
        form = SheetForm(instance=sheet)
        post_data = {field.name: field.value() or "foo" for field in form}
        # Put invalid TeX in title so that LaTeX log contains non-ASCII output
        post_data["title"] = "\\ø"
        # Click the print submit button
        post_data["print"] = "1"
        post_data["print_mode"] = SheetForm.PDF
        url = reverse("regnskab:krydsliste:sheet_update", kwargs=dict(pk=sheet.pk))
        response = self.client.post(url, post_data)
        self.assertIn("Fejl:", response.rendered_content)


class FormatPersonsTest(unittest.TestCase):
    def test_exact(self):
        output = Sheet.format_persons(['Foo', 'Bar'], rows=2)
        self.assertEquals('\\person{Foo}\n\\person{Bar}', output)

    def test_more(self):
        output = Sheet.format_persons(['Foo', 'Bar', 'Baz'], rows=2)
        self.assertEquals('\\person{Foo}\n\\person{Bar}', output)

    def test_less(self):
        output = Sheet.format_persons(['Foo', 'Bar'], rows=3)
        self.assertEquals('\\person{Foo}\n\\person{Bar}\n\\person{}', output)
