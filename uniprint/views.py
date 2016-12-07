from django.core.http import HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.views.generic import (
    TemplateView, FormView, CreateView,
)
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


printout_permission_required = permission_required('uniprint.add_printout')
printout_permission_required_method = method_decorator(
    printout_permission_required)


class DocumentCreate(CreateView):
    model = Document
    fields = ('file',)

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        document = form.save(commit=False)

        document.save()


class PrintoutCreate(CreateView):
    model = Printout
    fields = ('document', 'printer', 'duplex')

    @printout_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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
            try:
                printer = Printer.objects.get()
            except Exception:  # No printers or multiple printers
                printer = None
        else:
            printer = get_object_or_404(
                Printer.objects, pk=printer_id)
        return dict(document=document, printer=printer)

    def form_valid(self, form):
        printout = form.save(commit=False)
        try:
            printout.send_to_printer()
        except ValidationError as exn:
            form.add_error(None, exn)
            return self.form_invalid(form)
        printout.save()
        url = reverse('home')
        return HttpResponseRedirect(url + '?print=success')
