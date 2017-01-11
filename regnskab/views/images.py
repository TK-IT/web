import io
import json
import base64
import logging
import itertools
import collections

from django.core.urlresolvers import reverse
from django.views.generic import (
    FormView, View, TemplateView,
)
from django.shortcuts import get_object_or_404
from django.utils.html import format_html, format_html_join
from django.http import HttpResponse

from regnskab.models import SheetImage, Purchase
from .auth import regnskab_permission_required_method
from regnskab.images.quadrilateral import (
    Quadrilateral, extract_quadrilateral,
)
from regnskab.images.forms import (
    SheetImageCrossesForm, SheetImageParametersForm,
)
from regnskab.images.extract import (
    extract_images, plot_extract_rows_cols,
)

import numpy as np

import PIL


logger = logging.getLogger('regnskab')


class SheetImageList(TemplateView):
    template_name = 'regnskab/sheet_image_list.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        qs = SheetImage.objects.all()
        qs = qs.order_by('sheet', 'page')
        groups = itertools.groupby(qs, key=lambda o: o.sheet_id)
        sheets = []
        for sheet_id, g in groups:
            sheet_images = list(g)
            sheets.append((sheet_images[0].sheet, sheet_images))
        context_data['sheets'] = sheets
        return context_data


class SheetImageMixin:
    def get_sheet_image(self):
        return get_object_or_404(
            SheetImage.objects, sheet__pk=self.kwargs['pk'],
            page=self.kwargs['page'])


class SheetImageFile(View, SheetImageMixin):
    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        sheet_image = self.get_sheet_image()
        im_data = sheet_image.get_image()
        if self.kwargs.get('projected'):
            quad = Quadrilateral(sheet_image.quad)
            im_data = extract_quadrilateral(im_data, quad)
        im_data = (255 * im_data).astype(np.uint8)
        img = PIL.Image.fromarray(im_data)
        output = io.BytesIO()
        img.save(output, 'PNG')
        return HttpResponse(
            content=output.getvalue(),
            content_type='image/png')


class SheetImageCrosses(FormView, SheetImageMixin):
    form_class = SheetImageCrossesForm
    template_name = 'regnskab/sheet_image_crosses.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        sheet_image = self.get_sheet_image()
        context_data['image_url'] = reverse(
            'regnskab:sheet_image_file_projected',
            kwargs=dict(pk=sheet_image.sheet_id, page=sheet_image.page))
        context_data['layout'] = json.dumps(
            {'rows': sheet_image.rows, 'cols': sheet_image.cols},
            indent=2)
        return context_data

    def get_form_kwargs(self, **kwargs):
        r = super().get_form_kwargs(**kwargs)
        r['instance'] = self.get_sheet_image()
        return r

    def form_valid(self, form):
        o = self.get_sheet_image()
        o.crosses = form.get_crosses()
        o.boxes = form.get_boxes()
        o.compute_person_counts()
        if form.cleaned_data['verified']:
            o.set_verified(self.request.user)
        o.save()
        return self.render_to_response(
            self.get_context_data(form=form, saved=True))


class SheetImageParameters(FormView, SheetImageMixin):
    form_class = SheetImageParametersForm
    template_name = 'regnskab/sheet_image_parameters.html'

    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        r = super().get_form_kwargs(**kwargs)
        r['parameters'] = self.get_sheet_image().parameters
        return r

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        computed = []
        sheet_image = self.get_sheet_image()
        for k in 'quad cols rows person_rows'.split():
            d = getattr(sheet_image, k)
            shape = np.asarray(d).shape
            v = json.dumps(d, indent=2)
            computed.append(('%s (%s)' % (k, '×'.join(map(str, shape))), v))
        context_data['computed'] = computed

        fig = plot_extract_rows_cols(sheet_image)
        png_buf = io.BytesIO()
        fig.savefig(png_buf, format='png')
        png_b64 = base64.b64encode(png_buf.getvalue()).decode()
        context_data['fig_url'] = 'data:image/png;base64,%s' % png_b64

        return context_data

    def form_valid(self, form):
        sheet_image = self.get_sheet_image()
        for k in sheet_image.parameters.keys() & form.cleaned_data.keys():
            sheet_image.parameters[k] = form.cleaned_data[k]
        sheet = sheet_image.sheet
        sheet_image.save()  # Save parameters
        images, rows, purchases = extract_images(
            sheet, list(sheet.purchasekind_set.all()))
        sheet_image, = [im for im in images if im.page == sheet_image.page]
        sheet_image.save()
        if form.cleaned_data['reset']:
            sheet.sheetrow_set.all().delete()
            for o in rows:
                o.save()
            for o in purchases:
                o.row = o.row  # Update row_id
            Purchase.objects.bulk_create(purchases)
        return self.render_to_response(
            self.get_context_data(form=form, saved=True))


def get_sheetimage_cross_classes(qs):
    from regnskab.images.extract import get_crosses_from_counts

    pos = []
    neg = []
    for o in qs:
        imgs, coords = get_crosses_from_counts(o)
        c = collections.Counter(coords)
        dup = {k: v for k, v in c.items() if v > 1}
        assert not dup, dup
        coords = frozenset(coords)
        for i, row in enumerate(imgs):
            for j, img in enumerate(row):
                if (i, j) in coords:
                    pos.append(img)
                else:
                    neg.append(img)
    return pos, neg


def img_tag(im_data, **kwargs):
    from regnskab.images.utils import save_png

    png_data = save_png(im_data.reshape((24, 24, 3)))
    png_b64 = base64.b64encode(png_data).decode()
    return format_html(
        '<img src="data:image/png;base64,{}" {}/>', png_b64,
        format_html_join('', '{}="{}" ', kwargs.items()))


class Svm(View):
    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        pos, neg = get_sheetimage_cross_classes(
            SheetImage.objects.all()[0:4])
        pos = [im.ravel() for im in pos]
        neg = [im.ravel() for im in neg]

        from sklearn.svm import SVC

        svm = SVC(C=1e3, kernel='linear')
        svm.fit(pos + neg, [1] * len(pos) + [0] * len(neg))

        result = []

        sv_labels = svm.predict(svm.support_vectors_)
        sv_and_labels = list(zip(svm.support_vectors_, sv_labels))
        result.extend(img_tag(im)
                      for im, label in sv_and_labels
                      if label == 0)
        result.append('<hr />')
        result.extend(img_tag(im)
                      for im, label in sv_and_labels
                      if label == 1)
        result.append('<hr />')

        result.extend(img_tag(im) for im, label in
                      zip(pos, svm.predict(pos))
                      if label == 0)
        result.append('<hr />')
        result.extend(img_tag(im) for im, label in
                      zip(neg, svm.predict(neg))
                      if label == 1)

        return HttpResponse(''.join(result))


class NaiveParam(View):
    @regnskab_permission_required_method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        pos, neg = get_sheetimage_cross_classes(
            list(SheetImage.objects.all()[0:4]) +
            list(SheetImage.objects.all()[6:8]))

        from regnskab.images.extract import naive_cross_value
        pos = sorted(((im, naive_cross_value(im)) for im in pos),
                     key=lambda x: x[1])
        neg = sorted(((im, naive_cross_value(im)) for im in neg),
                     key=lambda x: x[1])
        neg_max = max(v for im, v in neg)
        pos_min = min(v for im, v in pos)
        neg_certain = ((im, v) for im, v in neg if v < pos_min)
        neg_maybe = ((im, v) for im, v in neg if v >= pos_min)
        pos_maybe = ((im, v) for im, v in pos if v < neg_max)
        pos_certain = ((im, v) for im, v in pos if v >= neg_max)

        def value_tag(x):
            return img_tag(x[0], title=str(x[1]))

        imgss = [neg_certain, neg_maybe, pos_maybe, pos_certain]
        return HttpResponse('<hr />'.join(
            ''.join(map(value_tag, imgs))
            for imgs in imgss))
