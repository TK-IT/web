import io
import logging
from django.conf import settings
from django.views.generic import ListView, CreateView, UpdateView
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from tkweb.apps.krydsliste.models import Sheet
from tkweb.apps.krydsliste.forms import SheetForm
from tkweb.apps.regnskab.views.auth import regnskab_permission_required_method
from tkweb.apps.regnskab.texrender import tex_to_pdf, RenderError
from tkweb.apps.regnskab.views import BalancePrint

try:
    from tkweb.apps.uniprint.api import print_new_document
except ImportError:
    from tkweb.apps.regnskab.texrender import print_new_document

logger = logging.getLogger('regnskab')


class SheetDelete(View):
    queryset = Sheet.objects.filter(deleted_time=None).order_by('-created_time')

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        for k, v in self.request.POST.items():
            if not v:
                continue
            p = "delete_krydsliste_"
            if k.startswith(p):
                try:
                    i = int(k.partition(p)[2])
                except Exception:
                    continue
                delete_ids.append(i)
        if delete_ids:
            Sheet.objects.filter(deleted_time=None, id__in=delete_ids).update(
                deleted_time=timezone.now()
            )


class SheetList(ListView):
    queryset = Sheet.objects.filter(deleted_time=None).order_by('-created_time')

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class PrintMixin:
    def get_tex_source(self):
        template = get_template('krydsliste/template.tex')
        context = {
            'title': self.object.title,
            'left_label': self.object.left_label,
            'right_label': self.object.right_label,
            'column1': self.object.column1,
            'column2': self.object.column2,
            'column3': self.object.column3,
            'front_persons': self.object.front_persons,
            'back_persons': self.object.back_persons,
        }
        return template.render(context)

    def handle_print(self, form):
        mode = form.cleaned_data['print_mode']

        tex_source = self.get_tex_source()
        if mode == SheetForm.SOURCE:
            return HttpResponse(tex_source,
                                content_type='text/plain; charset=utf8')

        try:
            pdf = tex_to_pdf(tex_source)
        except RenderError as exn:
            form.add_error(None, str(exn) + ': ' + exn.output)
            return self.form_invalid(form)

        if mode == SheetForm.PDF:
            return HttpResponse(pdf, content_type='application/pdf')

        if mode != SheetForm.PRINT:
            raise ValueError(mode)

        filename = 'krydsliste_%s.pdf' % self.object.pk
        username = self.request.user.username
        fake = settings.DEBUG
        copies = form.cleaned_data['copies']
        try:
            output = print_new_document(io.BytesIO(pdf),
                                        filename=filename,
                                        username=username,
                                        printer='A2',
                                        copies=copies,
                                        duplex=False, fake=fake)
        except Exception as exn:
            if settings.DEBUG and not isinstance(exn, ValidationError):
                raise
            form.add_error(None, str(exn))
            return self.form_invalid(form)

        logger.info("%s: Udskriv %s× krydsliste id=%s på A2",
                    self.request.user, copies, self.object.pk)

        url = reverse('regnskab:krydsliste:sheet_update',
                      kwargs=dict(pk=self.object.id),
                      current_app=self.request.resolver_match.namespace)
        return HttpResponseRedirect(url + '?print=success')


class SheetCreate(CreateView, PrintMixin):
    form_class = SheetForm
    template_name = 'krydsliste/sheet_form.html'

    def get_success_url(self):
        return reverse('regnskab:krydsliste:sheet_update',
                       kwargs=dict(pk=self.object.pk))

    def get_initial(self):
        initial = self.get_standard()
        try:
            n = int(self.request.GET['highscore'])
        except (KeyError, ValueError):
            pass
        else:
            if n <= 100:
                initial['front_persons'] = self.get_highscore(count=n)
            else:
                initial['front_persons'] = self.get_highscore(limit=n)
        return initial

    def get_standard(self):
        try:
            standard = Sheet.objects.filter(name='Standard')[0]
        except IndexError:
            return {}
        return {
            'title': standard.title,
            'left_label': standard.left_label,
            'right_label': standard.right_label,
            'column1': standard.column1,
            'column2': standard.column2,
            'column3': standard.column3,
            'front_persons': standard.front_persons,
            'back_persons': standard.back_persons,
        }

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_highscore(self, count=None, limit=None):
        context = BalancePrint.get_tex_context_data()
        personer = sorted(
            context['personer'], key=lambda p: p['total']['betalt'], reverse=True
        )
        if count is not None:
            personer = personer[:count]
        if limit is not None:
            personer = [p for p in personer if p['total']['betalt'] >= limit]
        names = [p['alias'] for p in personer]
        return Sheet.format_persons(names)


class SheetUpdate(UpdateView, PrintMixin):
    form_class = SheetForm
    model = Sheet
    template_name = 'krydsliste/sheet_form.html'

    def get_success_url(self):
        return reverse('regnskab:krydsliste:sheet_update',
                       kwargs=dict(pk=self.object.pk))

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['print'] = self.request.GET.get('print')
        return context_data

    def form_valid(self, form):
        self.object = form.save()
        if self.request.POST.get('print'):
            return self.handle_print(form)
        else:
            return HttpResponseRedirect(self.get_success_url())

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
