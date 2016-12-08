import os
import shlex
import logging
import tempfile
import subprocess

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User


logger = logging.getLogger('uniprint')


class Document(models.Model):
    file = models.FileField()
    text = models.TextField(blank=True, null=True)
    pages = models.IntegerField()
    pdfinfo = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

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


class Printout(models.Model):
    document = models.ForeignKey(Document, on_delete=models.SET_NULL,
                                 null=True, blank=False)
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL,
                                null=True, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField(auto_now_add=True)

    copies = models.PositiveIntegerField(default=1)
    duplex = models.BooleanField(blank=True, default=True)

    def __str__(self):
        return '<Printout %s on %s>' % (self.document, self.printer)

    def send_to_printer(self):
        host = '%s:%s' % (self.printer.hostname, self.printer.port)
        destination = self.printer.destination
        if self.duplex:
            opt = ('-o', 'Duplex=DuplexNoTumble')
        else:
            opt = ('-o', 'Duplex=None')

        filename = self.document.file.name
        cmd = ('lp', '-h', host, '-d', destination) + opt + (filename,)
        logger.info('Running %s', ' '.join(map(shlex.quote, cmd)))
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        with p:
            output, _ = p.communicate()
        output_brief = output.splitlines()[0][:100]
        if p.returncode != 0:
            logger.error(
                'lp return code was %s, output: %r',
                (p.returncode, output_brief))
            raise ValidationError(
                'lp return code was %s, output: %r' %
                (p.returncode, output_brief))
        logger.info('lp output: %r', output_brief)
        return output
