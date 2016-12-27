import io
import logging
import tempfile

from django.views.generic import (
    CreateView, UpdateView, DetailView, FormView,
)
from django.views.generic.detail import (
    BaseDetailView, SingleObjectMixin,
)
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse

from regnskab.models import Sheet, SheetImage
from .auth import regnskab_permission_required_method
from regnskab.images.utils import imagemagick_page_count
from regnskab.images.extract import (
    extract_quad, extract_rows_cols, extract_crosses,
)
from regnskab.images.forms import SheetImageForm

import PIL


logger = logging.getLogger('regnskab')


class SheetImageFile(BaseDetailView):
    model = SheetImage

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['session'])
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context):
        img = PIL.Image.fromarray(self.object.get_image())
        output = io.BytesIO()
        img.save(output, 'PNG')
        return HttpResponse(
            content=output.getvalue(),
            content_type='image/png')


class SheetImageUpdate(FormView):
    form_class = SheetImageForm
    template_name = 'regnskab/sheet_image_update.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        self.regnskab_session = get_object_or_404(
            Session.objects, pk=kwargs['session'])
        if not self.regnskab_session or self.regnskab_session.sent:
            return already_sent_view(request, self.regnskab_session)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(SheetImage.objects, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['object'] = self.get_object()
        return context_data

    def get_form_kwargs(self, **kwargs):
        r = super().get_form_kwargs(**kwargs)
        r['instance'] = self.get_object()
        return r

    def form_valid(self, form):
        o = self.get_object()
        o.crosses = form.get_crosses()
        o.compute_person_counts()
        o.save()
        return  # TODO
