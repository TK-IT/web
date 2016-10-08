from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from regnskab.forms import SheetCreateForm
from regnskab.models import Sheet


class SheetCreate(FormView):
    form_class = SheetCreateForm

    def form_valid(self, form):
        data = form.cleaned_data
        s = Sheet(name=data['name'],
                  start_date=data['start_date'],
                  end_date=data['end_date'])
        s.save()
        return redirect('sheet', pk=s.pk)


class SheetDetail(TemplateView):
    def get_sheet(self):
        return get_object_or_404(Sheet.objects, pk=self.kwargs['pk'])
