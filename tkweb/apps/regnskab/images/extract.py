from typing import Any, Tuple, Optional, List, TYPE_CHECKING, NamedTuple

from django.core.files.base import ContentFile
import numpy as np
import scipy.ndimage
import scipy.signal

from .parameters import Parameters, default_parameters
from .utils import save_png
from .quadrilateral import Quadrilateral, extract_quadrilateral

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa


if TYPE_CHECKING:
    from ..models import SheetImage, SheetRow, Purchase, Sheet


def contrast_stretch(
    im: np.ndarray, parameters: Parameters
) -> np.ndarray:
    q = parameters.contrast_stretch_q
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


def to_grey(im: np.ndarray, parameters: Parameters) -> np.ndarray:
    if im.ndim == 3:
        im = contrast_stretch(im, parameters=parameters)
        return im.min(axis=2)
    else:
        return im


def max_object(labels: np.ndarray, max_label: int) -> Tuple[int, int, int]:
    objects: List[Tuple[slice, slice]] = scipy.ndimage.find_objects(labels, max_label)

    def slice_length(s: slice, axis: int) -> int:
        start, stop, stride = s.indices(labels.shape[axis])
        return stop - start

    def object_area(o: Optional[Tuple[slice, slice]]) -> int:
        if o is None:
            return 0
        else:
            return slice_length(o[0], 0) * slice_length(o[1], 1)

    object_areas = [object_area(o) for o in objects]
    mo = np.argmax(object_areas)

    return (
        mo + 1,
        object_areas[mo],
        np.sum(labels == mo + 1),
    )


def find_bbox(
    im: np.ndarray, parameters: Parameters
) -> Quadrilateral:
    sigma = parameters.find_bbox_sigma
    margin1 = parameters.find_bbox_margin1
    threshold = parameters.find_bbox_threshold
    im = im[int(margin1):-int(margin1), int(margin1):-int(margin1)]
    if sigma > 0.01:
        im = scipy.ndimage.filters.gaussian_filter(im, sigma, mode='constant')
    dark = (im < threshold)

    labels, no_labels = scipy.ndimage.label(dark)
    (label, area, count) = max_object(labels, no_labels)
    obj = np.zeros((im.shape[0] + 2*int(margin1), im.shape[1] + 2*int(margin1)))
    obj[int(margin1):-int(margin1), int(margin1):-int(margin1)] = (labels == label) * 1.0
    ys, xs = (labels == label).nonzero()
    top_left = np.argmax(-xs - ys / 2)
    top_right = np.argmax(xs - ys / 2)  # Top right not used, see below
    bottom_right = np.argmax(xs + ys)
    bottom_left = np.argmax(-xs + ys)

    corners = np.transpose(
        [[xs[i], ys[i]]
         for i in (top_left, top_right, bottom_right, bottom_left)])
    # Set top_right to be top_left + (bottom_right - bottom_left)
    corners[:, 1] = corners[:, 0] + (corners[:, 2] - corners[:, 3])
    corners += int(margin1)
    return Quadrilateral(corners), obj


def extract_quad(sheet_image: "SheetImage") -> None:
    parameters = get_parameters(sheet_image)
    put_parameters(sheet_image, parameters)
    quad, obj = find_bbox(to_grey(sheet_image.get_image(),
                                  parameters),
                          parameters=parameters)
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


class PeaksResult(NamedTuple):
    peaks: Any
    cutoff: Any
    min_cutoff: Any
    max_cutoff: Any
    opt_cutoff: Any


def find_peaks(
    xs: np.ndarray, cutoff: float, skip_start=True, skip_end=True, full=False
) -> PeaksResult:
    xs = np.asarray(xs).ravel()
    n = len(xs)
    above = xs > cutoff
    above_pad = np.r_[False, above, False]
    is_start = above_pad[1:-1] & ~above_pad[0:-2]
    is_end = above_pad[1:-1] & ~above_pad[2:]
    start = is_start.nonzero()[0]
    end = is_end.nonzero()[0]
    assert len(start) == len(end)
    peaks = []
    for i, j in zip(start, end):
        peaks.append(i + np.argmax(xs[i:j+1]))
    peaks = np.array(peaks, dtype=np.intp)
    m = np.median(np.diff(peaks))
    # TODO Make 1/3 configurable
    if skip_start:
        peaks = peaks[peaks > m/3]
    if skip_end:
        peaks = peaks[peaks < n - m/3]
    if not full:
        return peaks
    maxima = scipy.signal.argrelmax(xs)[0]
    maxima_vals = xs[maxima]
    min_cutoff = np.max(maxima_vals[maxima_vals <= cutoff])
    max_cutoff = np.min(maxima_vals[maxima_vals > cutoff])
    opt_cutoff = min_cutoff + (max_cutoff - min_cutoff) / 2
    return PeaksResult(
        peaks, cutoff, min_cutoff, max_cutoff, opt_cutoff)


def get_name_part(sheet_image: "SheetImage", input: np.ndarray) -> np.ndarray:
    k = int(sheet_image.cols[0] * input.shape[1])
    return input[:, :k]


def get_crosses_part(sheet_image: "SheetImage", input: np.ndarray) -> np.ndarray:
    k = int(sheet_image.cols[0] * input.shape[1])
    return input[:, k:]


def extract_cols(
    sheet_image: "SheetImage", input_grey: np.ndarray, parameters: Parameters
) -> None:
    cutoff = parameters.extract_cols_cutoff
    image_width = input_grey.shape[1]
    col_avg = np.mean(input_grey, axis=0)
    col_peaks = find_peaks(-col_avg, -cutoff)
    sheet_image.cols = fill_in_skipped(
        (col_peaks / image_width).tolist() + [1])


def extract_rows(
    sheet_image: "SheetImage", input_grey: np.ndarray, parameters: Parameters
) -> None:
    cutoff = parameters.extract_rows_cutoff
    crosses_grey = get_crosses_part(sheet_image, input_grey)
    height = crosses_grey.shape[0]
    row_avg = np.mean(crosses_grey, axis=1)
    row_peaks = find_peaks(-row_avg, -cutoff)
    sheet_image.rows = fill_in_skipped(
        [0] + (row_peaks / height).tolist() + [1])


def extract_person_rows(
    sheet_image: "SheetImage", input_grey: np.ndarray, parameters: Parameters
) -> None:
    cutoff = parameters.extract_person_rows_cutoff
    names_grey = get_name_part(sheet_image, input_grey)
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


def extract_rows_cols(sheet_image: "SheetImage") -> None:
    parameters = get_parameters(sheet_image)
    put_parameters(sheet_image, parameters)
    im = sheet_image.get_image()
    input_bbox = Quadrilateral(sheet_image.quad)

    input_transform = extract_quadrilateral(im, input_bbox)
    input_grey = to_grey(input_transform, parameters)

    extract_cols(sheet_image, input_grey, parameters)
    extract_rows(sheet_image, input_grey, parameters)
    extract_person_rows(sheet_image, input_grey, parameters)


def plot_extract_rows_cols(sheet_image: "SheetImage") -> plt.Figure:
    parameters = get_parameters(sheet_image)
    im = sheet_image.get_image()
    input_bbox = Quadrilateral(sheet_image.quad)

    input_transform = extract_quadrilateral(im, input_bbox)
    input_grey = to_grey(input_transform, parameters)
    names_grey = get_name_part(sheet_image, input_grey)
    crosses_grey = get_crosses_part(sheet_image, input_grey)

    fig, (ax1, ax2, ax3) = plt.subplots(3)

    col_avg = np.mean(input_grey, axis=0)
    ax1.plot(np.arange(len(col_avg)) / (len(col_avg) - 1), col_avg, 'k-')
    col_cutoff = parameters.extract_cols_cutoff
    ax1.plot([0, 1], [col_cutoff, col_cutoff], 'r-')
    col_peak_data = find_peaks(-col_avg, -col_cutoff, full=True)
    col_peaks = col_peak_data.peaks
    ax1.plot(col_peaks / (len(col_avg) - 1), col_avg[col_peaks], '.')

    row_avg = np.mean(crosses_grey, axis=1)
    ax2.plot(np.arange(len(row_avg)) / (len(row_avg) - 1), row_avg, 'k-')
    row_cutoff = parameters.extract_rows_cutoff
    ax2.plot([0, 1], [row_cutoff, row_cutoff], 'r-')
    row_peak_data = find_peaks(-row_avg, -row_cutoff, full=True)
    row_peaks = row_peak_data.peaks
    ax2.plot(row_peaks / (len(row_avg) - 1), row_avg[row_peaks], '.')

    name_avg = np.mean(names_grey, axis=1, keepdims=True)
    ax3.plot(np.arange(len(name_avg)) / (len(name_avg) - 1), name_avg, 'k-')
    name_cutoff = parameters.extract_person_rows_cutoff
    name_peak_data = find_peaks(-name_avg, -name_cutoff, full=True)
    name_peaks = name_peak_data.peaks
    ax3.plot([0, 1], [name_cutoff, name_cutoff], 'r-')
    ax3.plot(name_peaks / (len(name_avg) - 1), name_avg[name_peaks], '.')

    # print(col_peak_data.opt_cutoff)
    # print(row_peak_data.opt_cutoff)
    # print(name_peak_data.opt_cutoff)
    return fig


def extract_cross_images(sheet_image: "SheetImage") -> List[List[np.ndarray]]:
    im = sheet_image.get_image()
    quad = Quadrilateral(sheet_image.quad)
    input_transform = extract_quadrilateral(im, quad)

    height, width, _depth = input_transform.shape

    rows = np.multiply(sheet_image.rows, height).astype(np.intp)
    cols = np.multiply(sheet_image.cols, width).astype(np.intp)

    cross_imgs: List[List[np.ndarray]] = []
    for i, (y1, y2) in enumerate(zip(rows[:-1], rows[1:])):
        cross_imgs.append([])
        for j, (x1, x2) in enumerate(zip(cols[:-1], cols[1:])):
            cross_imgs[-1].append(input_transform[y1:y2, x1:x2])
    assert len(cross_imgs) == len(rows) - 1

    return cross_imgs


def naive_cross_value(data: np.ndarray) -> float:
    if data.max() > 1:
        data = data / data.max()
    height, width, depth = data.shape
    i, j = np.mgrid[0:height, 0:width].astype(np.float)
    neg_i = (height - 1) - i
    neg_j = (width - 1) - j
    weights = np.minimum(
        np.minimum(i, neg_i) / (height - 1),
        np.minimum(j, neg_j) / (width - 1),
    )
    weights = weights ** 2
    weights /= weights.sum() * depth
    return ((1 - data) * weights[:, :, np.newaxis]).sum()
    # return (v - lo) / (hi - lo)


def extract_crosses(
    sheet_image: "SheetImage"
) -> None:
    parameters = get_parameters(sheet_image)
    put_parameters(sheet_image, parameters)
    lo = parameters.extract_crosses_lo
    hi = parameters.extract_crosses_hi
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


def get_sheet_rows(sheet_image: "SheetImage") -> List["SheetRow"]:
    from tkweb.apps.regnskab import models
    prev_pages = models.SheetImage.objects.filter(
        sheet=sheet_image.sheet,
        page__lt=sheet_image.page,
    )
    prev_person_count = sum(len(o.person_rows) for o in prev_pages)
    n = len(sheet_image.person_rows)
    # Note position is 1-indexed
    qs = models.SheetRow.objects.filter(
        sheet=sheet_image.sheet,
        position__gte=prev_person_count + 1,
        position__lte=prev_person_count + n,
    )
    sheet_rows = list(qs)
    assert len(sheet_rows) == len(sheet_image.person_rows)
    return sheet_rows


def get_cross_counts(
    sheet_image: "SheetImage", kinds: List[str]
) -> List[List[Tuple[int, int]]]:
    from tkweb.apps.regnskab import models
    sheet_rows = get_sheet_rows(sheet_image)
    purchase_kinds = list(sheet_image.sheet.purchasekind_set.all())
    purchases = {
        (p.row_id, p.kind_id): p
        for p in models.Purchase.objects.filter(row__sheet=sheet_image.sheet)
    }
    result: List[List[Tuple[int, int]]] = []
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


def get_crosses_from_field(
    cross_imgs: List[List[np.ndarray]],
    singles: int,
    boxes: int,
    row_offset: int,
    col_offset: int,
) -> List[Tuple[int, int]]:
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

    crosses: List[Tuple[int, int]] = []
    remaining: List[Tuple[int, int]] = []

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


def get_crosses_from_counts(
    sheet_image: "SheetImage", parameters: Parameters
) -> Tuple[List[List[np.ndarray]], List[List[Tuple[int, int]]]]:
    øl = parameters.get_person_crosses_øl
    guldøl = parameters.get_person_crosses_guldøl
    sodavand = parameters.get_person_crosses_sodavand
    KINDS = 'øl guldøl sodavand'.split()
    cross_counts = get_cross_counts(sheet_image, KINDS)
    assert sum(sheet_image.person_rows) == len(sheet_image.rows) - 1
    cross_imgs = extract_cross_images(sheet_image)
    col_bounds = np.cumsum([0, øl, guldøl, sodavand])
    assert sum(sheet_image.person_rows) == len(cross_imgs)
    row_bounds = np.cumsum([0] + sheet_image.person_rows)
    n = len(sheet_image.person_rows)

    cross_coordinates: List[List[Tuple[int, int]]] = []

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


def get_person_crosses(
    person_rows: List[int], parameters: Parameters
) -> List[Tuple[int, float]]:
    øl = parameters.get_person_crosses_øl
    guldøl = parameters.get_person_crosses_guldøl
    sodavand = parameters.get_person_crosses_sodavand
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
        groups.append((crosses, box_crosses/2))
    return groups


def get_images(sheet: "Sheet") -> List["SheetImage"]:
    from tkweb.apps.regnskab import models
    if sheet.pk:
        existing = list(models.SheetImage.objects.filter(sheet=sheet))
        if existing:
            for o in existing:
                o.get_image()
            return existing
    images: List[np.ndarray] = []
    with sheet.image_file_name():
        i = 1
        while i < 1000:
            try:
                im = models.SheetImage(sheet=sheet, page=i)
                im.get_image()
                images.append(im)
            except Exception:
                if i == 1:
                    raise
                break
            i += 1
    return images


def get_parameters(sheet_image: "SheetImage") -> Parameters:
    # Translate '.' to '_' in parameters
    d = {k.replace(".", "_"): v for k, v in sheet_image.parameters.items()}
    return Parameters(**{
        k: d.get(k, getattr(default_parameters, k))
        for k in Parameters._fields
    })


def put_parameters(sheet_image: "SheetImage", parameters: Parameters) -> None:
    sheet_image.parameters = parameters._asdict()


def extract_images(
    sheet: "Sheet", kinds: List[str]
) -> Tuple[List["SheetImage"], Any, Any]:
    images = get_images(sheet)
    for sheet_image in images:
        extract_quad(sheet_image)
        extract_rows_cols(sheet_image)
        extract_crosses(sheet_image)

    rows, purchases, png_file = extract_row_image(sheet, kinds, images)
    sheet.row_image = png_file
    return images, rows, purchases


def rerun_extract_images(sheet):
    kinds = list(sheet.purchasekind_set.all())
    images, rows, purchases = extract_images(sheet, kinds)
    if len(rows) != len(sheet.sheetrow_set.all()):
        raise ValueError("Wrong number of existing SheetRows")
    for r1, r2 in zip(sheet.sheetrow_set.all(), rows):
        r1.image_start, r1.image_stop = r2.image_start, r2.image_stop
        r1.save()
    sheet.save()
    for im in images:
        im.save()


def extract_row_image(
    sheet: "Sheet", kinds: List[str], images: List["SheetImage"]
) -> Tuple[List["SheetRow"], List["Purchase"], ContentFile]:
    from tkweb.apps.regnskab import models
    rows: List["SheetRow"] = []
    purchases: List["Purchase"] = []

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

            y1, y2 = im_rows[i], im_rows[j]
            corners = quad.to_world([[0, 1, 1, 0], [y1, y1, y2, y2]])
            person_quad = Quadrilateral(corners)
            stitched_image.append(extract_quadrilateral(
                im.get_image(), person_quad, width, height=None))
            height = stitched_image[-1].shape[0]

            rows.append(
                models.SheetRow(
                    sheet=sheet,
                    position=position,
                    image_start=stitched_image_height,
                    image_stop=stitched_image_height + height,
                )
            )

            p_crosses = get_person_crosses(im.crosses[i:j],
                                           parameters=im.parameters)
            for col_idx, (count, boxcount) in enumerate(p_crosses):
                kind, boxkind = kinds[2*col_idx:2*(col_idx+1)]
                if count:
                    purchases.append(models.Purchase(
                        row=rows[-1],
                        kind=kind,
                        count=count))
                if boxcount:
                    purchases.append(models.Purchase(
                        row=rows[-1],
                        kind=boxkind,
                        count=boxcount))

            stitched_image_height += height
            i = j
            position += 1

    stitched_image = np.concatenate(stitched_image)

    from django.utils import timezone

    png_data = save_png(stitched_image)
    png_name = timezone.now().strftime('rows-%Y-%m-%d.png')
    png_file = ContentFile(png_data, png_name)
    return rows, purchases, png_file
