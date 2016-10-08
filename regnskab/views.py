from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, FormView
from regnskab.forms import SheetCreateForm
from regnskab.models import Sheet


class SheetCreate(FormView):
    form_class = SheetCreateForm
    template_name = 'regnskab/sheet_create.html'

    def form_valid(self, form):
        data = form.cleaned_data
        s = Sheet(name=data['name'],
                  start_date=data['start_date'],
                  end_date=data['end_date'])
        s.save()
        return redirect('sheet', pk=s.pk)


class SheetDetail(TemplateView):
    template_name = 'regnskab/sheet_detail.html'

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetDetail, self).get_context_data(**kwargs)
        context_data['sheet'] = self.get_sheet()
        return context_data
