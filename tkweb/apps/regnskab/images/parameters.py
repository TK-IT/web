import inspect
import functools
from typing import Callable, TypeVar, Dict, NamedTuple


Parameters = NamedTuple("Parameters", [
    ("contrast_stretch_q", float),
    ("find_bbox_sigma", float),
    ("find_bbox_margin1", int),
    ("find_bbox_threshold", float),
    ("extract_cols_cutoff", float),
    ("extract_rows_cutoff", float),
    ("extract_person_rows_cutoff", float),
    ("extract_crosses_lo", float),
    ("extract_crosses_hi", float),
    ("get_person_crosses_øl", int),
    ("get_person_crosses_guldøl", int),
    ("get_person_crosses_sodavand", int),
])


default_parameters = Parameters(
    contrast_stretch_q=0.02,
    find_bbox_sigma=1.0,
    find_bbox_margin1=1,
    find_bbox_threshold=0.6,
    extract_cols_cutoff=0.39,
    extract_rows_cutoff=0.6,
    extract_person_rows_cutoff=0.27,
    extract_crosses_lo=0.030,
    extract_crosses_hi=0.045,
    get_person_crosses_øl=15,
    get_person_crosses_guldøl=6,
    get_person_crosses_sodavand=15,
)
