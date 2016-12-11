from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from uniprint.models import Document, Printout
from uniprint.document import (
    extract_plain_text, get_pdfinfo, pages_from_pdfinfo,
    FileTypeError,
)


def create_document(fp, filename, username):
    if not hasattr(fp, 'open') and not isinstance(fp, bytes):
        fp = fp.read()
    if isinstance(fp, bytes):
        fp = ContentFile(fp, filename)
    document = Document(file=fp)
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


def print_document(document, printer, username,
                   copies=1, duplex=True, page_range=None,
                   fake=False):
    printout = Printout(document=document,
                        copies=copies, duplex=duplex,
                        page_range=page_range)
    try:
        printout.created_by = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValueError('user')
    printout.clean()
    if not fake:
        printout.send_to_printer()
    return printout


def print_new_document(fp, filename, username, **kwargs):
    document = create_document(fp, filename=filename, username=username)
    try:
        return print_document(document, username=username, **kwargs)
    except:
        if document.pk:
            document.delete()
        raise
