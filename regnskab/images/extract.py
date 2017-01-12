from collections import namedtuple

import numpy as np
import scipy.ndimage
import scipy.signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from django.core.files.base import ContentFile
from django.utils import timezone

from .parameters import parameter
from .utils import save_png
from .quadrilateral import Quadrilateral, extract_quadrilateral
from regnskab.models import (
    SheetImage, SheetRow, Purchase,
)


@parameter('q')
def contrast_stretch(im, q=0.02):
    if im.ndim == 2:
        im_channels = im[:, :, np.newaxis]
    else:
        im_channels = im
    im_channels = im_channels.astype(np.float)

    pct = q * 100
    fractiles = np.percentile(im_channels, [pct, 100 - pct], (0, 1),
                              interpolation='nearest', keepdims=True)
    mins, maxs = fractiles
    return np.minimum(1, np.maximum(0, (im - mins) / (maxs - mins)))


def to_grey(im, parameters):
    if im.ndim == 3:
        im = contrast_stretch(im, parameters=parameters)
        return im.min(axis=2)
    else:
        return im


def max_object(labels, max_label, k):
    objects = scipy.ndimage.find_objects(labels, max_label)

    def slice_length(s, axis):
        start, stop, stride = s.indices(labels.shape[axis])
        return stop - start

    def object_area(o):
        if o is None:
            return 0
        else:
            return slice_length(o[0], 0) * slice_length(o[1], 1)

    object_areas = np.fromiter(map(object_area, objects), dtype=np.int)
    if k == 1:
        mos = [np.argmax(object_areas)]
    else:
        mos = reversed(list(np.argsort(object_areas)[-5:]))

    return [
        (mo + 1,
         object_areas[mo],
         np.sum(labels == mo + 1))
        for mo in mos
    ]


@parameter('sigma margin1 threshold')
def find_bbox(im, sigma=1, margin1=10, threshold=0.6):
    im = im[margin1:-margin1, margin1:-margin1]
    if sigma > 0.01:
        im = scipy.ndimage.filters.gaussian_filter(im, sigma, mode='constant')
    dark = (im < threshold)

    labels, no_labels = scipy.ndimage.label(dark)
    (label, area, count), = max_object(labels, no_labels, 1)
    obj = np.zeros((im.shape[0] + 2*margin1, im.shape[1] + 2*margin1))
    obj[margin1:-margin1, margin1:-margin1] = (labels == label) * 1.0
    ys, xs = (labels == label).nonzero()
    top_left = np.argmax(-xs - ys / 2)
    bottom_right = np.argmax(xs + ys)
    bottom_left = np.argmax(-xs + ys)
    top_right = np.argmax(xs - ys / 2)

    corners = np.transpose(
        [[xs[i], ys[i]]
         for i in (top_left, top_right, bottom_right, bottom_left)])
    corners += margin1
    return Quadrilateral(corners), obj


def extract_quad(sheet_image):
    quad, obj = find_bbox(to_grey(sheet_image.get_image(),
                                  sheet_image.parameters),
                          parameters=sheet_image.parameters)
    sheet_image.quad = quad.arg().tolist()


def fill_in_skipped(xs):
    diff = np.diff(xs)
    m = np.median(diff)
    # We expect every row height to be roughly m.
    # If a row height is more than 1.5 m, we skipped a row.
    skipped = np.round((diff - m) / m)
    fixed = []
    for y, extra in zip(xs[:-1], skipped):
        fixed.append(y)
        for i in range(int(extra)):
            fixed.append(y + (i+1) * m)
    fixed.append(xs[-1])
    return fixed


PeaksResult = namedtuple(
    'PeaksResult', 'peaks cutoff min_cutoff max_cutoff opt_cutoff'.split())


def find_peaks(xs, cutoff, skip_start=True, skip_end=True, full=False):
    xs = np.asarray(xs).ravel()
    n = len(xs)
    above = xs > cutoff
    above_pad = np.r_[False, above, False]
    is_start = above_pad[1:-1] & ~above_pad[0:-2]
    is_end = above_pad[1:-1] & ~above_pad[2:]
    start = is_start.nonzero()[0]
    end = is_end.nonzero()[0]
    print(start)
    print(end)
    assert len(start) == len(end)
    peaks = []
    for i, j in zip(start, end):
        peaks.append(i + np.argmax(xs[i:j+1]))
    print(n, peaks)
    peaks = np.array(peaks, dtype=np.intp)
    m = np.median(np.diff(peaks))
    if skip_start:
        peaks = peaks[peaks > m/2]
    if skip_end:
        peaks = peaks[peaks < n - m/2]
    if not full:
        return peaks
    maxima = scipy.signal.argrelmax(xs)[0]
    maxima_vals = xs[maxima]
    min_cutoff = np.max(maxima_vals[maxima_vals <= cutoff])
    max_cutoff = np.min(maxima_vals[maxima_vals > cutoff])
    opt_cutoff = min_cutoff + (max_cutoff - min_cutoff) / 2
    return PeaksResult(
        peaks, cutoff, min_cutoff, max_cutoff, opt_cutoff)


def get_name_part(sheet_image, input_grey, resolution=None):
    name_rect = [[0, sheet_image.cols[0], sheet_image.cols[0], 0],
                 [0, 0, 1, 1]]
    name_quad = Quadrilateral(
        np.asarray([[input_grey.shape[1]], [input_grey.shape[0]]]) *
        np.asarray(name_rect))
    return extract_quadrilateral(
        input_grey, name_quad, resolution, resolution)


@parameter('cutoff')
def extract_cols(sheet_image, input_grey, cutoff=0.5):
    image_width = input_grey.shape[1]
    col_avg = np.mean(input_grey, axis=0)
    col_peaks = find_peaks(-col_avg, -cutoff)
    sheet_image.cols = fill_in_skipped(
        (col_peaks / image_width).tolist() + [1])


@parameter('cutoff')
def extract_rows(sheet_image, input_grey, cutoff=0.8):
    height = input_grey.shape[0]
    row_avg = np.mean(input_grey, axis=1)
    row_peaks = find_peaks(-row_avg, -cutoff)
    sheet_image.rows = fill_in_skipped(
        [0] + (row_peaks / height).tolist() + [1])


@parameter('cutoff')
def extract_person_rows(sheet_image, input_grey, cutoff=0.5):
    resolution = max(input_grey.shape)
    names_grey = get_name_part(sheet_image, input_grey, resolution)
    height = names_grey.shape[0]
    row_avg = np.mean(names_grey, axis=1, keepdims=True)
    row_peaks = find_peaks(-row_avg, -cutoff) / height

    rows = np.asarray(sheet_image.rows)
    closest = np.abs(row_peaks.reshape(-1, 1) -
                     rows.reshape(1, -1)).argmin(1)
    sheet_image.person_rows = np.diff(
        [0] + closest.tolist() + [len(rows)-1]).tolist()
    if any(v == 0 for v in sheet_image.person_rows):
        raise Exception('Person has no rows: %s' %
                        (sheet_image.person_rows,))


def extract_rows_cols(sheet_image):
    im = sheet_image.get_image()
    input_bbox = Quadrilateral(sheet_image.quad)

    resolution = max(im.shape)
    input_transform = extract_quadrilateral(
        im, input_bbox, resolution, resolution)
    input_grey = to_grey(input_transform, sheet_image.parameters)

    extract_cols(sheet_image, input_grey)
    extract_rows(sheet_image, input_grey)
    extract_person_rows(sheet_image, input_grey)


def plot_extract_rows_cols(sheet_image):
    im = sheet_image.get_image()
    input_bbox = Quadrilateral(sheet_image.quad)

    resolution = max(im.shape)
    input_transform = extract_quadrilateral(
        im, input_bbox, resolution, resolution)
    input_grey = to_grey(input_transform, sheet_image.parameters)
    names_grey = get_name_part(sheet_image, input_grey, resolution)

    fig, (ax1, ax2, ax3) = plt.subplots(3)

    sz = resolution - 1
    col_avg = np.mean(input_grey, axis=0)
    ax1.plot(np.arange(resolution) / sz, col_avg, 'k-')
    col_cutoff = sheet_image.parameters['extract_cols.cutoff']
    ax1.plot([0, 1], [col_cutoff, col_cutoff], 'r-')
    col_peaks = find_peaks(-col_avg, -col_cutoff)
    ax1.plot(col_peaks / sz, col_avg[col_peaks], '.')

    row_avg = np.mean(input_grey, axis=1)
    ax2.plot(np.arange(resolution) / sz, row_avg, 'k-')
    row_cutoff = sheet_image.parameters['extract_rows.cutoff']
    ax2.plot([0, 1], [row_cutoff, row_cutoff], 'r-')
    row_peaks = find_peaks(-row_avg, -row_cutoff)
    ax2.plot(row_peaks / sz, row_avg[row_peaks], '.')

    name_row_avg = np.mean(names_grey, axis=1, keepdims=True)
    ax3.plot(np.arange(resolution) / sz, name_row_avg, 'k-')
    name_row_cutoff = sheet_image.parameters['extract_person_rows.cutoff']
    name_row_peaks = find_peaks(-name_row_avg, -name_row_cutoff)
    ax3.plot([0, 1], [name_row_cutoff, name_row_cutoff], 'r-')
    ax3.plot(name_row_peaks / sz, name_row_avg[name_row_peaks], '.')

    return fig


def extract_cross_images(sheet_image):
    im = sheet_image.get_image()
    quad = Quadrilateral(sheet_image.quad)

    rows = sheet_image.rows
    cols = sheet_image.cols

    width = height = 24
    cross_imgs = []
    for i, (y1, y2) in enumerate(zip(rows[:-1], rows[1:])):
        cross_imgs.append([])
        for j, (x1, x2) in enumerate(zip(cols[:-1], cols[1:])):
            top_left = (x1, y1)
            top_right = (x2, y1)
            bottom_right = (x2, y2)
            bottom_left = (x1, y2)
            corners = quad.to_world(np.transpose([
                top_left, top_right, bottom_right, bottom_left]))
            cross = Quadrilateral(corners)
            cross_imgs[-1].append(extract_quadrilateral(
                im, cross, width, height))
    assert len(cross_imgs) == len(rows) - 1

    return cross_imgs


def naive_cross_value(data):
    if data.max() > 1:
        data = data / data.max()
    height, width, depth = data.shape
    i, j = np.mgrid[0:height, 0:width].astype(np.float)
    neg_i = (height - 1) - i
    neg_j = (width - 1) - j
    weights = np.minimum(
        np.minimum(i, neg_i),
        np.minimum(j, neg_j),
    )
    weights = weights ** 2
    weights /= weights.sum() * depth
    return ((1 - data) * weights[:, :, np.newaxis]).sum()
    # return (v - lo) / (hi - lo)


@parameter('lo hi')
def extract_crosses(sheet_image, lo=0.030, hi=0.045):
    cross_imgs = extract_cross_images(sheet_image)
    values = [
        [naive_cross_value(c) for c in row]
        for row in cross_imgs
    ]
    # Treat values <= lo as "definitely False"
    # and values >= hi as "definitely True".
    # Mark values between lo and hi as True if they are between
    # two entries that are definitely True.
    labels = []
    for value_row in values:
        row = [bool(v >= hi) for v in value_row]
        prev_decided = 0
        for i, v in enumerate(value_row):
            if not (lo < v < hi):
                if row[i] and row[prev_decided]:
                    # Mark everything in-between these definitely True
                    # as True.
                    row[prev_decided:i] = (i-prev_decided)*[True]
                prev_decided = i
        labels.append(row)
    sheet_image.crosses = labels


def get_sheet_rows(sheet_image):
    prev_pages = SheetImage.objects.filter(sheet=sheet_image.sheet,
                                           page__lt=sheet_image.page)
    prev_person_count = sum(len(o.person_rows) for o in prev_pages)
    n = len(sheet_image.person_rows)
    # Note position is 1-indexed
    qs = SheetRow.objects.filter(sheet=sheet_image.sheet,
                                 position__gte=prev_person_count + 1,
                                 position__lte=prev_person_count + n)
    sheet_rows = list(qs)
    assert len(sheet_rows) == len(sheet_image.person_rows)
    return sheet_rows


def get_cross_counts(sheet_image, kinds):
    sheet_rows = get_sheet_rows(sheet_image)
    purchase_kinds = list(sheet_image.sheet.purchasekind_set.all())
    purchases = {
        (p.row_id, p.kind_id): p
        for p in Purchase.objects.filter(row__sheet=sheet_image.sheet)
    }
    result = []
    for sheet_row in sheet_rows:
        singles = {}
        boxes = {}
        for kind in purchase_kinds:
            try:
                p = purchases[sheet_row.id, kind.id]
            except KeyError:
                continue
            if kind.name.endswith('kasse'):
                boxes[kind.name[:-5]] = p.count
            else:
                singles[kind.name] = p.count
        result.append([
            (singles.get(kind, 0), boxes.get(kind, 0))
            for kind in kinds
        ])
    return result


def get_crosses_from_field(cross_imgs, singles, boxes, row_offset, col_offset):
    assert cross_imgs, cross_imgs
    if singles == boxes == 0:
        return []
    n = len(cross_imgs)
    m = len(cross_imgs[0])
    values = {
        (i, j): naive_cross_value(c)
        for i, row in enumerate(cross_imgs)
        for j, c in enumerate(row)
    }
    order = sorted(values.keys(), key=lambda k: values[k], reverse=True)
    rank = {k: i for i, k in enumerate(order)}
    min_extra = int(2*boxes)
    if singles + min_extra > n*m:
        # User put in too many crosses.
        # We can't do better than mark everything as a cross.
        print("Warning: Too many crosses (%s and %s boxes for %sx%s)" %
              (singles, boxes, n, m))
        return [(i + row_offset, j + col_offset)
                for i in range(n) for j in range(m)]
    assert singles + min_extra <= n*m
    max_extra = min(int(4*boxes), n*m - singles)
    assert 0 <= min_extra <= max_extra <= n*m - singles

    crosses = []
    remaining = []

    # Add all strong crosses that are filled up from the left or right.
    for i in range(n):
        if all(rank[i, j] < singles + min_extra for j in range(m)):
            # Entire row is crossed.
            crosses.extend((i, j) for j in range(m))
        else:
            row_singles = next(j for j in range(m)
                               if rank[i, j] >= singles + min_extra)
            row_boxes = next(j for j in range(m, 0, -1)
                             if rank[i, j-1] >= singles + min_extra)
            # FIXME: Don't take too many crosses on the right,
            # but use max_extra to limit this.
            crosses.extend((i, j) for j in range(0, row_singles))
            remaining.extend((i, j) for j in range(row_singles, row_boxes))
            crosses.extend((i, j) for j in range(row_boxes, m))
    assert len(crosses) <= singles + min_extra

    # There must be at least (singles + min_extra) crosses,
    # so 'certain_cross' is the value of the "weakest" certain cross.
    certain_cross = values[order[singles + min_extra - 1]]
    # There are at most (singles + max_extra) crosses,
    # so 'certain_not_cross' is the value of the "strong" certain not-cross.
    if singles + max_extra < n*m:
        certain_not_cross = values[order[singles + max_extra]]
    else:
        certain_not_cross = 0
    # Keep up to (singles + max_extra) - len(crosses) from remaining
    # that have value greater than 'threshold'.
    threshold = certain_not_cross + (certain_cross - certain_not_cross) / 2
    remaining.sort(key=lambda k: values[k], reverse=True)
    for k in remaining[:singles + max_extra - len(crosses)]:
        if values[k] > threshold:
            crosses.append(k)
    assert singles + min_extra <= len(crosses) <= singles + max_extra
    return [(i + row_offset, j + col_offset) for i, j in crosses]


@parameter('get_person_crosses.øl',
           'get_person_crosses.guldøl',
           'get_person_crosses.sodavand')
def get_crosses_from_counts(sheet_image, øl=15, guldøl=6, sodavand=15):
    KINDS = 'øl guldøl sodavand'.split()
    cross_counts = get_cross_counts(sheet_image, KINDS)
    assert sum(sheet_image.person_rows) == len(sheet_image.rows) - 1
    cross_imgs = extract_cross_images(sheet_image)
    col_bounds = np.cumsum([0, øl, guldøl, sodavand])
    assert sum(sheet_image.person_rows) == len(cross_imgs)
    row_bounds = np.cumsum([0] + sheet_image.person_rows)
    n = len(sheet_image.person_rows)

    cross_coordinates = []

    for person_index in range(n):
        r1, r2 = row_bounds[person_index], row_bounds[person_index+1]
        for kind_index in range(len(KINDS)):
            c1, c2 = col_bounds[kind_index], col_bounds[kind_index+1]
            singles, boxes = cross_counts[person_index][kind_index]
            assert singles == int(singles)
            assert 0 <= r1 < r2 <= len(cross_imgs), (r1, r2, len(cross_imgs))
            add = get_crosses_from_field(
                [row[c1:c2] for row in cross_imgs[r1:r2]],
                int(singles), boxes, r1, c1)
            assert all(r1 <= r < r2 for r, c in add), add
            assert all(c1 <= c < c2 for r, c in add), add
            assert len(set(add)) == len(add), add
            cross_coordinates.extend(add)
    return cross_imgs, cross_coordinates


@parameter('øl guldøl sodavand')
def get_person_crosses(person_rows, øl=15, guldøl=6, sodavand=15):
    col_bounds = np.cumsum([0, øl, guldøl, sodavand])
    groups = []
    for i, j in zip(col_bounds[:-1], col_bounds[1:]):
        group_rows = [r[i:j] for r in person_rows]
        crosses = box_crosses = 0
        for r in group_rows:
            try:
                x = next(i for i in range(len(r))
                         if not r[len(r)-1-i])
            except StopIteration:
                x = 0
            r_crosses = sum(r) - x
            crosses += r_crosses
            box_crosses += x
        groups.append([crosses, box_crosses/2])
    return groups


def get_images(sheet):
    if sheet.pk:
        existing = list(SheetImage.objects.filter(sheet=sheet))
        if existing:
            for o in existing:
                o.get_image()
            return existing
    images = []
    with sheet.image_file_name():
        i = 1
        while i < 1000:
            try:
                im = SheetImage(sheet=sheet, page=i)
                im.get_image()
                images.append(im)
            except Exception:
                if i == 1:
                    raise
                break
            i += 1
    return images


def extract_images(sheet, kinds):
    images = get_images(sheet)
    for im in images:
        extract_quad(im)
        extract_rows_cols(im)
        extract_crosses(im)

    rows, purchases, png_file = extract_row_image(sheet, kinds, images)
    sheet.row_image = png_file
    return images, rows, purchases


def extract_row_image(sheet, kinds, images):
    rows = []
    purchases = []

    stitched_image = []
    stitched_image_height = 0
    sheet.row_image_width = width = 920
    position = 1
    for im in images:
        quad = Quadrilateral(im.quad)
        im_rows = im.rows
        i = 0
        for person_row_count in im.person_rows:
            assert person_row_count != 0
            j = i + person_row_count

            height = 20 * (j - i)
            y1, y2 = im_rows[i], im_rows[j]
            corners = quad.to_world([[0, 1, 1, 0], [y1, y1, y2, y2]])
            person_quad = Quadrilateral(corners)
            stitched_image.append(extract_quadrilateral(
                im.get_image(), person_quad, width, height))

            rows.append(SheetRow(sheet=sheet, position=position,
                                 image_start=stitched_image_height,
                                 image_stop=stitched_image_height + height))

            p_crosses = get_person_crosses(im.crosses[i:j],
                                           parameters=im.parameters)
            for col_idx, (count, boxcount) in enumerate(p_crosses):
                kind, boxkind = kinds[2*col_idx:2*(col_idx+1)]
                if count:
                    purchases.append(Purchase(
                        row=rows[-1],
                        kind=kind,
                        count=count))
                if boxcount:
                    purchases.append(Purchase(
                        row=rows[-1],
                        kind=boxkind,
                        count=boxcount))

            stitched_image_height += height
            i = j
            position += 1

    stitched_image = np.concatenate(stitched_image)
    png_data = save_png(stitched_image)
    png_name = timezone.now().strftime('rows-%Y-%m-%d.png')
    png_file = ContentFile(png_data, png_name)
    return rows, purchases, png_file
