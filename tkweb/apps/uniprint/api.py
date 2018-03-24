'''
The functions in this module allow applications to print PDFs via uniprint.
There are two modes of operation: interactive and non-interactive.
If the user should be able to pick printing options (destination, # copies, ...),
then the interactive mode should be used:

    document = create_document(pdf_fp, 'filename.pdf', request.user.username)
    url = print_url(document)
    # Redirect the user to 'url' which lets the user create the printout.

If all options are given along with the PDF, the noninteractive mode can be used:
    printout = print_new_document(
        pdf_fp, 'filename.pdf', request.user.username,
        printer='A2', option='twosided',
        # plus any other arguments of print_document you may want
    )
'''
import shlex
import logging

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from uniprint.models import Document, Printout, Printer
from uniprint.document import (
    extract_plain_text, get_pdfinfo, pages_from_pdfinfo,
)
from uniprint.options import Options, Option


logger = logging.getLogger('uniprint')


def create_document(fp, filename, username):
    if not hasattr(fp, 'open') and not isinstance(fp, bytes):
        fp = fp.read()
    if isinstance(fp, bytes):
        fp = ContentFile(fp, filename)
    size = len(fp)
    document = Document(file=fp, size=size)
    try:
        document.created_by = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValueError('user')
    document.original_filename = filename
    document.pdfinfo = get_pdfinfo(document.file)
    document.text = extract_plain_text(document.file)
    document.pages = pages_from_pdfinfo(document.pdfinfo)
    document.save()
    return document


def print_url(document):
    return reverse('printout_create') + '?d=%s' % document.pk


def print_document(document, printer, username,
                   copies=1, duplex=None, page_range=None,
                   fake=False, option=None):

    if duplex is not None and option is not None:
        raise TypeError("Cannot mix 'duplex' and 'option'")
    elif duplex is not None:
        if duplex is True:
            option = Options.twosided
        elif duplex is False:
            option = Options.onesided
        else:
            raise ValueError(duplex)

    if isinstance(option, str):
        try:
            options_entry = getattr(Options, option)
        except AttributeError:
            pass
        else:
            if isinstance(options_entry, Option):
                option = options_entry

    if isinstance(option, str):
        option_string = option
    elif isinstance(option, list):
        option_string = ' '.join(o.lp_string() for o in option)
    else:
        option_string = option.lp_string()

    if isinstance(printer, str):
        try:
            printer = Printer.objects.get(name=printer)
        except Printer.DoesNotExist:
            raise ValueError(printer)
    printout = Printout(document=document, printer=printer,
                        copies=copies, lp_option_string=option_string,
                        page_range=page_range or '')
    try:
        printout.created_by = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValueError(username)
    printout.clean()
    if fake:
        cmdline = ' '.join(map(shlex.quote, printout.get_command_line()))
        logger.info('Fake: Not running %s', cmdline)
    else:
        printout.send_to_printer()
    printout.save()
    return printout


def print_new_document(fp, filename, username, **kwargs):
    # TODO: Switch this function to using Django transactions.
    # Currently we use poor man's transactions since nothing else
    # in our codebase uses real transactions.
    document = create_document(fp, filename=filename, username=username)
    try:
        return print_document(document, username=username, **kwargs)
    except:
        if document.pk:
            document.delete()
        raise
