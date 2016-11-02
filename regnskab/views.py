from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, FormView
from regnskab.forms import SheetCreateForm
from regnskab.models import Sheet, SheetRow


class SheetCreate(FormView):
    form_class = SheetCreateForm
    template_name = 'regnskab/sheet_create.html'

    def form_valid(self, form):
        data = form.cleaned_data
        s = Sheet(name=data['name'],
                  start_date=data['start_date'],
                  end_date=data['end_date'])
        s.save()
        for i, kind in enumerate(data['kinds']):
            s.purchasekind_set.create(
                name=kind['name'],
                position=i + 1,
                price=kind['price'])
        return redirect('sheet', pk=s.pk)


class SheetDetail(TemplateView):
    template_name = 'regnskab/sheet_detail.html'

    def get(self, request, *args, **kwargs):
        s = self.get_sheet()
        qs = SheetRow.objects.filter(sheet=s)
        if not qs.exists():
            return redirect('sheet_update', pk=s.pk)
        else:
            return super().get(request, *args, **kwargs)

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetDetail, self).get_context_data(**kwargs)
        context_data['sheet'] = self.get_sheet()
        return context_data


class SheetUpdate(TemplateView):
    template_name = 'regnskab/sheet_update.html'

    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super(SheetUpdate, self).get_context_data(**kwargs)
        context_data['sheet'] = self.get_sheet()
        return context_data
