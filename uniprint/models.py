import os
import shlex
import logging
import tempfile
import subprocess

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify as dslugify
from unidecode import unidecode


def slugify(string):
    return dslugify(unidecode(string))


def document_path(instance, input_filename):
    filename = os.path.basename(input_filename)
    base, ext = os.path.splitext(filename)
    slug_base = slugify(base)
    slug_name = slug_base + ext
    username = instance.created_by.username
    return '/'.join(('uniprint', username, slug_name))


logger = logging.getLogger('uniprint')


class Document(models.Model):
    file = models.FileField(upload_to=document_path)
    original_filename = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    size = models.BigIntegerField()
    pages = models.IntegerField()
    pdfinfo = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        s = 'side' if self.pages == 1 else 'sider'
        return '%s (%s %s)' % (self.original_filename, self.pages, s)

    class Meta:
        ordering = ['created_time']


class Printer(models.Model):
    name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)

    @property
    def hostname(self):
        return 'localhost'

    @property
    def port(self):
        return 6631

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


def page_range_ranges(s):
    parts = s.split(',')
    for p in parts:
        try:
            s, e = p.split('-')
        except ValueError:
            s, e = p, p
        try:
            r = range(int(s), int(e)+1)
        except ValueError:
            raise ValidationError('%r er ikke et heltal' % (v,))
        if len(r) == 0:
            raise ValidationError('%s-%s er et ugyldigt interval' %
                                  (s, e))
        yield r


def page_range_page_count(s, d):
    if s:
        return sum(len(r) for r in page_range_ranges(s))
    else:
        return d


def validate_page_range(s, pages):
    for r in page_range_ranges(s):
        if not (1 <= r.start <= r.stop - 1 <= pages):
            raise ValidationError('Dokumentet har kun %s sider' %
                                  pages)


class Printout(models.Model):
    document = models.ForeignKey(Document, on_delete=models.SET_NULL,
                                 null=True, blank=False)
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL,
                                null=True, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    copies = models.PositiveIntegerField(default=1)
    lp_option_string = models.TextField(blank=True)
    duplex = models.BooleanField(blank=True, default=True)
    page_range = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '<Printout %s on %s>' % (self.document, self.printer)

    def clean(self):
        if self.page_range:
            validate_page_range(self.page_range, self.document.pages)

    @property
    def page_range_page_count(self):
        return page_range_page_count(self.page_range, self.document.pages)

    @property
    def page_count(self):
        return self.copies * self.page_range_page_count

    @property
    def sheet_count(self):
        if self.duplex:
            return self.copies * ((1 + self.page_range_page_count) // 2)
        else:
            return self.page_count

    def send_to_printer(self):
        host = '%s:%s' % (self.printer.hostname, self.printer.port)
        destination = self.printer.destination

        filename = self.document.file.path
        cmd = ('lp', '-h', host, '-d', destination)
        if self.copies != 1:
            cmd += ('-n', str(self.copies))
        if self.duplex:
            cmd += ('-o', 'Duplex=DuplexNoTumble')
        else:
            cmd += ('-o', 'Duplex=None')
        if self.page_range:
            cmd += ('-P', self.page_range)
        if self.created_by:
            cmd += ('-U', self.created_by.username)
        cmd += (filename,)
        cmdline = ' '.join(map(shlex.quote, cmd))
        logger.info('Running %s', cmdline)
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        with p:
            try:
                output, _ = p.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                p.terminate()
                try:
                    p.wait(timeout=0.1)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=0.1)
                msg = '%s timed out' % cmdline
                logger.error(msg)
                raise ValidationError(msg)
        output_lines = output.splitlines() or ('',)
        output_brief = output_lines[0][:100]
        if p.returncode != 0:
            msg = ('%s return code was %s, ' % (cmdline, p.returncode) +
                   'output: %r' % output_brief)
            logger.error(msg)
            raise ValidationError(msg)
        logger.info('lp output: %r', output_brief)
        return output
