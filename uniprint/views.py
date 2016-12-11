from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.views.generic import (
    TemplateView, FormView, CreateView, ListView,
)
from django import forms
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.db.models import Max

from uniprint.models import Document, Printer, Printout
from uniprint.document import (
    extract_plain_text, get_pdfinfo, pages_from_pdfinfo,
    FileTypeError,
)
from uniprint.api import create_document, print_document


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
        doc_dummy = form.save(commit=False)
        file = doc_dummy.file
        try:
            document = create_document(
                fp=file, filename=form.cleaned_data['file'].name,
                username=self.request.user.username,
            )
        except FileTypeError as exn:
            form.add_error('file', 'Du skal angive en PDF')
            return self.form_invalid(form)
        except Exception as exn:
            logger.exception('Could not parse uploaded PDF')
            form.add_error(None, 'Ukendt fejl: %s' % (exn,))
            return self.form_invalid(form)
        url = reverse('printout_create')
        return HttpResponseRedirect(url + '?d=%s' % document.pk)


class DocumentList(ListView):
    template_name = 'uniprint/document_list.html'
    paginate_by = 100

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Document.objects.all()
        username = self.kwargs.get('username')
        if username is not None:
            qs = qs.filter(created_by__username=username)
        qs = qs.order_by('created_time')
        qs = qs.annotate(
            latest_printout=Max('printout__created_time'))
        return qs


class PrintoutList(ListView):
    template_name = 'uniprint/printout_list.html'
    paginate_by = 100

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Printout.objects.all()
        username = self.kwargs.get('username')
        if username is not None:
            qs = qs.filter(created_by__username=username)
        qs = qs.order_by('created_time')
        return qs


class PrintoutCreate(CreateView):
    template_name = 'uniprint/printout_create.html'
    model = Printout
    fields = ('document', 'printer', 'copies', 'duplex', 'page_range')

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if settings.DEBUG:
            form.fields['fake'] = forms.BooleanField(
                required=False, initial=True, label='DEBUG: Kun en prøve')
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
        dummy = form.save(commit=False)
        fake = bool(form.cleaned_data.get('fake'))
        try:
            printout = print_document(
                dummy.document, printer=dummy.printer,
                username=self.request.user.username,
                copies=dummy.copies, duplex=dummy.duplex,
                page_range=dummy.page_range, fake=fake)
        except ValidationError as exn:
            form.add_error(None, exn)
            return self.form_invalid(form)
        url = reverse('home')
        return HttpResponseRedirect(url + '?print=success')
