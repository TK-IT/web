import numpy as np
import scipy.ndimage
import scipy.signal

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
    return (im - mins) / (maxs - mins)


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


@parameter('sigma margin1 margin2 margin3 threshold')
def find_bbox(im, sigma=1, margin1=10, margin2=100, margin3=20, threshold=0.6):
    im = im[margin1:-margin1, margin1:-margin1]
    if sigma > 0.01:
        im = scipy.ndimage.filters.gaussian_filter(im, sigma, mode='constant')
    dark = (im < threshold)

    # dark is boolean, so argmax returns the first true
    left = np.argmax(dark, axis=1)
    # left[i] is the index of the first dark cell in row i
    left = np.amin(left[margin2:-margin2])
    # left is the row with the first dark cell

    # multiply by arange to make argmax select the last true in each row
    right = np.argmax(dark * np.arange(dark.shape[1])[np.newaxis, :], axis=1)
    # right[i] is the index of the last dark cell in row i
    right = np.max(right[margin2:-margin2])

    top = np.argmax(dark, axis=0)
    top = np.max(top[left + margin3:right - margin3])
    bottom = np.argmax(dark * np.arange(dark.shape[0])[:, np.newaxis], axis=0)
    bottom = np.max(bottom[left + margin3:right - margin3])

    labels, no_labels = scipy.ndimage.label(dark)
    (label, area, count), = max_object(labels, no_labels, 1)
    obj = np.zeros((im.shape[0] + 2*margin1, im.shape[1] + 2*margin1))
    obj[margin1:-margin1, margin1:-margin1] = (labels == label) * 1.0
    ys, xs = (labels == label).nonzero()
    sums = xs + ys
    diffs = xs - ys
    top_left = np.argmin(sums)
    bottom_right = np.argmax(sums)
    bottom_left = np.argmin(diffs)
    top_right = np.argmax(diffs)

    corners = np.asarray(
        [[xs[i], ys[i]]
         for i in (top_left, top_right, bottom_right, bottom_left)])
    corners += margin1
    return Quadrilateral(corners), obj


def extract_quad(sheet_image):
    quad, obj = find_bbox(to_grey(sheet_image.get_image(),
                                  sheet_image.parameters),
                          parameters=sheet_image.parameters)
    sheet_image.quad = quad.arg().tolist()


@parameter('cutoff width max_distance')
def extract_cols(sheet_image, input_grey,
                 cutoff=100/255, width=4, max_distance=3):
    width = input_grey.shape[1]
    col_avg = np.mean(input_grey, axis=0, keepdims=True)
    col_peaks = np.asarray(scipy.signal.find_peaks_cwt(
        -np.minimum(col_avg, cutoff).ravel(), [width],
        max_distances=[max_distance]))
    sheet_image.cols = (col_peaks / width).tolist() + [1]


@parameter('cutoff width max_distance')
def extract_rows(sheet_image, input_grey,
                 cutoff=0, width=3, max_distance=3):
    height = input_grey.shape[0]
    row_avg = np.mean(input_grey, axis=1, keepdims=True)
    row_peaks = np.asarray(scipy.signal.find_peaks_cwt(
        -np.minimum(row_avg, cutoff).ravel(), [width],
        max_distances=[max_distance]))
    sheet_image.rows = [0] + (row_peaks / height).tolist() + [1]


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


@parameter('cutoff width max_distance')
def extract_person_rows(sheet_image, input_grey,
                        cutoff=0, width=3, max_distance=3):
    im = sheet_image.get_image()
    input_bbox = Quadrilateral(sheet_image.quad)
    resolution = max(im.shape)
    name_rect = [[0, sheet_image.cols[0], sheet_image.cols[0], 0],
                 [0, 0, 1, 1]]
    name_rect = input_bbox.to_world(name_rect)
    name_quad = Quadrilateral(name_rect.T)

    names_grey = extract_quadrilateral(
        input_grey, name_quad, resolution, resolution)
    height = names_grey.shape[0]
    row_avg = np.mean(names_grey, axis=1, keepdims=True)
    row_peaks = np.asarray(scipy.signal.find_peaks_cwt(
        -np.minimum(row_avg.ravel(), cutoff), [width],
        max_distances=[max_distance])) / height

    rows = np.r_[0, sheet_image.rows, 1]
    closest = np.abs(row_peaks.reshape(-1, 1) -
                     rows.reshape(1, -1)).argmin(1)
    sheet_image.person_rows = np.diff(
        [0] + closest.tolist() + [len(rows)-1]).tolist()
    if any(v == 0 for v in sheet_image.person_rows):
        raise Exception('Person has no rows')


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
            cross = Quadrilateral(np.transpose(corners))
            cross_imgs[-1].append(extract_quadrilateral(
                im, cross, width, height))

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
    weights /= weights.sum() * depth
    return ((1 - data) * weights[:, :, np.newaxis]).sum()
    # return (v - lo) / (hi - lo)


@parameter('lo hi')
def extract_crosses(sheet_image, lo=0.080, hi=0.116):
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
    values = {
        (i, j): naive_cross_value(c)
        for i, row in enumerate(cross_imgs)
        for j, c in enumerate(row)
    }
    order = sorted(values.keys(), key=lambda k: values[k], reverse=True)
    rank = {k: i for i, k in enumerate(order)}
    TODO


@parameter('get_person_crosses.øl',
           'get_person_crosses.guldøl',
           'get_person_crosses.sodavand')
def get_crosses_from_counts(sheet_image, øl=15, guldøl=6, sodavand=15):
    cross_counts = get_cross_counts(sheet_image)
    cross_imgs = extract_cross_images(sheet_image)
    KINDS = 'øl guldøl sodavand'.split()
    col_bounds = np.cumsum([0, øl, guldøl, sodavand])
    row_bounds = np.cumsum([0] + sheet_image.person_rows)
    n = len(sheet_image.person_rows)

    cross_coordinates = []

    for person_index in range(n):
        r1, r2 = row_bounds[person_index], row_bounds[person_index+1]
        for kind_index in len(KINDS):
            c1, c2 = col_bounds[kind_index], col_bounds[kind_index+1]
            singles, boxes = cross_counts[person_index][kind_index]
            cross_coordinates.extend(get_crosses_from_field(
                [row[c1:c2] for row in cross_imgs[r1:r2]], singles, boxes,
                r1, c1))
    return cross_coordinates


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


def extract_images(sheet, kinds):
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

    for im in images:
        extract_quad(im)
        extract_rows_cols(im)
        extract_crosses(im)

    stitched_image = []
    stitched_image_height = 0
    rows = []
    purchases = []
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
            corners = quad.to_world([[0, 1, 1, 0], [y1, y1, y2, y2]]).T
            person_quad = Quadrilateral(corners)
            stitched_image.append(extract_quadrilateral(
                im.get_image(), person_quad, width, height))

            rows.append(SheetRow(sheet=sheet, position=position,
                                 image_start=stitched_image_height,
                                 image_stop=stitched_image_height + height))

            p_crosses = get_person_crosses(im.crosses[i:j])
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
    sheet.row_image = png_file

    return images, rows, purchases
