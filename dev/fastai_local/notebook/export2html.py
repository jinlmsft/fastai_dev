#AUTOGENERATED! DO NOT EDIT! File to edit: dev/99a_export2html.ipynb (unless otherwise specified).

__all__ = ['remove_widget_state', 'hide_cells', 'add_show_docs']

from ..core import *

from ..test import *

from ..imports import *

from .export import *

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor, Preprocessor
from nbconvert import HTMLExporter
from nbformat.sign import NotebookNotary
from traitlets.config import Config

def remove_widget_state(cell):
    "Remove widgets in the output of `cells`"
    if cell['cell_type'] == 'code' and 'outputs' in cell:
        cell['outputs'] = [l for l in cell['outputs']
                           if not ('data' in l and 'application/vnd.jupyter.widget-view+json' in l.data)]
    return cell

def hide_cells(cell):
    "Hide cell that need to be hidden"
    for pat in [r'^\s*#\s*export\s+', r'^\s*#\s*hide\s+', r'^\s*#\s*default_exp\s+', r's*show_doc\(']:
        if check_re(cell, pat): cell['metadata'] = {'hide_input': True}
    return cell

def _show_doc_cell(name):
    return {'cell_type': 'code',
            'execution_count': None,
            'metadata': {},
            'outputs': [],
            'source': f"show_doc({name})"}

def add_show_docs(cells):
    "Add `show_doc` for each exported function or class"
    res = []
    for cell in cells:
        res.append(cell)
        if check_re(cell, r'^\s*#\s*exports?\s*'):
            names = func_class_names(cell['source'])
            for n in names: res.append(_show_doc_cell(n))
    return res