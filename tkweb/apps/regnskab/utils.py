import re
from unittest.mock import patch
from django.db.models import F, Sum
from django.utils import html, safestring
from django.core.mail import EmailMessage, SafeMIMEMultipart
import html2text
from django.conf import settings


def sum_vector(qs, index_spec, value_spec):
    """
    Sum queryset values, grouping over given dimension.

    sum_matrix(Foo.objects.all(), 'c', 'z') turns into the SQL query:

    SELECT Foo.c, SUM(Foo.z) FROM Foo GROUP BY Foo.c

    The result is a mapping `d` such that d[x]
    is the sum of z values where c = x.
    """
    qs = qs.order_by()
    qs = qs.annotate(index_spec=F(index_spec))
    qs = qs.values("index_spec")
    qs = qs.annotate(value_spec=Sum(value_spec))
    res = {}
    for record in qs:
        index = record.pop("index_spec")
        assert index not in res
        res[index] = record.pop("value_spec")
    return res


def sum_matrix(qs, column_spec, row_spec, value_spec):
    """
    Sum queryset values, grouping over two dimensions.

    sum_matrix(Foo.objects.all(), 'c1', 'c2', 'z') turns into the SQL query:

    SELECT Foo.c1, Foo.c2, SUM(Foo.z) FROM Foo GROUP BY Foo.c1, Foo.c2

    The result is a nested mapping `d` such that d[x1][x2]
    is the sum of z values where c1 = x1 and c2 = x2.
    """
    qs = qs.order_by()
    qs = qs.annotate(row_spec=F(row_spec), column_spec=F(column_spec))
    qs = qs.values("row_spec", "column_spec")
    qs = qs.annotate(value_spec=Sum(value_spec))
    res = {}
    for record in qs:
        row = record.pop("row_spec")
        column = record.pop("column_spec")
        value = record.pop("value_spec")
        cells = res.setdefault(column, {})
        assert row not in cells
        cells[row] = value
    return res


def line_to_html(line):
    strip = line.lstrip()
    leading_ws = len(line) - len(strip)
    return safestring.mark_safe(leading_ws * "&nbsp;" + html.escape(strip))


def plain_to_html(body):
    body = re.sub(r"\r\n|\r|\n", "\n", body.strip())
    paras = re.split(r"\n\n+", body)
    paras_html = []
    for p in paras:
        lines = p.split("\n")
        paras_html.append("<p>%s</p>" % "<br>\n".join(map(line_to_html, lines)))
    return safestring.mark_safe("\n".join(paras_html))


def html_to_plain(body):
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.unicode_snob = True
    h.images_to_alt = True
    h.body_width = 0
    with patch("html2text.escape_md_section", (lambda t, snob=False: t)):
        return h.handle(str(body))


class EmailMultiRelated(EmailMessage):
    """
    A version of EmailMessage that makes it easy to send multipart/related
    messages for HTML email with inline images.
    Based on EmailMultiAlternatives in Django.
    """

    related_subtype = "related"
    alternative_subtype = "alternative"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alternatives = []
        self.relateds = []

    def attach_alternative(self, content, mimetype):
        """Attach an alternative content representation."""
        assert content is not None
        assert mimetype is not None
        self.alternatives.append((content, mimetype))

    def attach_related(self, content, mimetype, cid):
        """Attach an alternative content representation."""
        assert content is not None
        assert mimetype is not None
        assert cid is not None
        self.relateds.append((content, mimetype, cid))

    def _create_message(self, msg):
        return self._create_attachments(
            self._create_relateds(self._create_alternatives(msg))
        )

    def _create_alternatives(self, msg):
        encoding = self.encoding or settings.DEFAULT_CHARSET
        if self.alternatives:
            body_msg = msg
            msg = SafeMIMEMultipart(
                _subtype=self.alternative_subtype, encoding=encoding
            )
            if self.body:
                msg.attach(body_msg)
            for alternative in self.alternatives:
                msg.attach(self._create_mime_attachment(*alternative))
        return msg

    def _create_relateds(self, msg):
        encoding = self.encoding or settings.DEFAULT_CHARSET
        if self.relateds:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.related_subtype, encoding=encoding)
            msg.attach(body_msg)
            for content, mimetype, cid in self.relateds:
                attachment = self._create_mime_attachment(content, mimetype)
                attachment["Content-ID"] = "<%s>" % cid
                attachment["Content-Disposition"] = "inline"
                msg.attach(attachment)
        return msg
