from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.views.generic import (
    TemplateView, FormView, CreateView,
)
from django import forms
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

from uniprint.models import Document, Printer, Printout
from uniprint.document import (
    extract_plain_text, get_pdfinfo, pages_from_pdfinfo,
    FileTypeError,
)


printout_permission_required = permission_required('uniprint.add_printout')
printout_permission_required_method = method_decorator(
    printout_permission_required)


class Home(TemplateView):
    template_name = 'uniprint/home.html'

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['print'] = self.request.GET.get('print')
        return context_data


class DocumentCreate(CreateView):
    template_name = 'uniprint/document_create.html'
    model = Document
    fields = ('file',)

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        document = form.save(commit=False)
        document.original_filename = form.cleaned_data['file'].name
        try:
            document.pdfinfo = get_pdfinfo(document.file)
            document.text = extract_plain_text(document.file)
            document.pages = pages_from_pdfinfo(document.pdfinfo)
        except FileTypeError as exn:
            form.add_error('file', 'Du skal angive en PDF')
            return self.form_invalid(form)
        except Exception as exn:
            logger.exception('Could not parse uploaded PDF')
            form.add_error(None, 'Ukendt fejl: %s' % (exn,))
            return self.form_invalid(form)
        document.created_by = self.request.user
        document.save()
        url = reverse('printout_create')
        return HttpResponseRedirect(url + '?d=%s' % document.pk)


class PrintoutCreate(CreateView):
    template_name = 'uniprint/printout_create.html'
    model = Printout
    fields = ('document', 'printer', 'duplex')

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if settings.DEBUG:
            form.fields['fake'] = forms.BooleanField(
                required=False, initial=True, label='Kun en prøve')
        return form

    def get_initial(self):
        try:
            document_id = self.request.GET['d']
        except KeyError:
            document = None
        else:
            document = get_object_or_404(
                Document.objects, pk=document_id)
        try:
            printer_id = self.request.GET['p']
        except KeyError:
            printer = None
        else:
            printer = get_object_or_404(
                Printer.objects, pk=printer_id)
        return dict(document=document, printer=printer)

    def form_valid(self, form):
        printout = form.save(commit=False)
        printout.created_by = self.request.user
        if not form.cleaned_data.get('fake'):
            try:
                printout.send_to_printer()
            except ValidationError as exn:
                form.add_error(None, exn)
                return self.form_invalid(form)
        printout.save()
        url = reverse('home')
        return HttpResponseRedirect(url + '?print=success')
