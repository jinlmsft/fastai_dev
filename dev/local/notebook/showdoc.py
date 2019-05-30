#AUTOGENERATED! DO NOT EDIT! File to edit: dev/92_notebook_showdoc.ipynb (unless otherwise specified).

__all__ = ['is_enum', 'add_pytorch_index', 'is_fastai_module', 'FASTAI_DOCS', 'doc_link', 'add_doc_links',
           'get_function_source', 'SOURCE_URL', 'get_source_link', 'FASTAI_NB_DEV', 'source_link', 'type_repr',
           'format_param', 'show_doc', 'md2html', 'doc']

from ..imports import *
from .core import *
from .export import *
import inspect,enum,nbconvert
from IPython.display import Markdown,display
from IPython.core import page
from nbconvert import HTMLExporter

def is_enum(cls):
    "Check if `cls` is an enum or another type of class"
    return cls.__class__ == enum.Enum or cls.__class__ == enum.EnumMeta

def _get_pytorch_index():
    if not (Path(__file__).parent/'index_pytorch.txt').exists(): return {}
    return json.load(open(Path(__file__).parent/'index_pytorch.txt', 'r'))

def add_pytorch_index(func_name, url):
    "Add `func_name` in the PyTorch index for automatic links."
    index = _get_pytorch_index()
    if not url.startswith("https://pytorch.org/docs/stable/"):
        url = "https://pytorch.org/docs/stable/" + url
    index[func_name] = url
    json.dump(index, open(Path(__file__).parent/'index_pytorch.txt', 'w'), indent=2)

def is_fastai_module(name):
    "Test if `name` is a fastai module."
    dir_name = os.path.sep.join(name.split('.'))
    return (Path(__file__).parent.parent/f"{dir_name}.py").exists()

#Might change once the library is renamed fastai.
def _is_fastai_class(ft): return belongs_to_module(ft, 'fastai_source')
def _strip_fastai(s): return re.sub(r'^local\.', '', s)
FASTAI_DOCS = ''

def doc_link(name, include_bt:bool=True):
    "Create link to documentation for `name`."
    cname = f'`{name}`' if include_bt else name
    #Link to modules
    if is_fastai_module(name): return f'[{cname}]({FASTAI_DOCS}/{name}.html)'
    #Link to fastai functions
    try_fastai = source_nb(name, is_name=True)
    if try_fastai:
        page = '.'.join(try_fastai.split('_')[1:]).replace('.ipynb', '.html')
        return f'[{cname}]({FASTAI_DOCS}/{page}#{name})'
    #Link to PyTorch
    try_pytorch = _get_pytorch_index().get(name, None)
    if try_pytorch: return f'[{cname}]({try_pytorch})'
    #Leave as is
    return cname

def add_doc_links(text):
    "Search for doc links for any item between backticks in `text`."
    pat = re.compile("\[`([^`]*)`\](?:\([^)]*\))|`([^`]*)`")
    def _replace_link(m): return doc_link(m.group(1) or m.group(2))
    return re.sub(pat, _replace_link, text)

SOURCE_URL = "https://github.com/fastai/fastai_docs/tree/master/dev/"

def get_function_source(func):
    "Return link to `func` in source code"
    try: line = inspect.getsourcelines(func)[1]
    except Exception: return ''
    module = inspect.getmodule(func).__name__.replace('.', '/') + '.py'
    return f"{SOURCE_URL}{module}#L{line}"

FASTAI_NB_DEV = 'https://nbviewer.jupyter.org/github/fastai/fastai_docs/blob/master/dev/'

def get_source_link(func, local=False, is_name=None):
    "Return a link to the notebook where `func` is defined."
    pref = '' if local else FASTAI_NB_DEV
    is_name = is_name or isinstance(func, str)
    src = source_nb(func, is_name=is_name, return_all=True)
    if src is None: return '' if is_name else get_function_source(func)
    find_name,nb_name = src
    nb = read_nb(nb_name)
    pat = re.compile(f'^{find_name}\s+=|^(def|class)\s+{find_name}\s*\(', re.MULTILINE)
    for i,cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code' and re.search(pat, cell['source']): break
    if re.search(pat, cell['source']) is None:
        return '' if is_name else get_function_source(func)
    header_pat = re.compile(r'^\s*#+\s*(.*)$')
    while i >= 0:
        cell = nb['cells'][i]
        if cell['cell_type'] == 'markdown' and re.search(header_pat, cell['source']):
            title = re.search(header_pat, cell['source']).groups()[0]
            anchor = '-'.join([s for s in title.split(' ') if len(s) > 0])
            return f'{pref}{nb_name}#{anchor}'
        i -= 1
    return f'{pref}{nb_name}'

def source_link(func, is_name=None, disp=True):
    "Show a relative link to the notebook where `func` is defined"
    is_name = is_name or isinstance(func, str)
    func_name = func if is_name else qual_name(func)
    link = get_source_link(func, local=True, is_name=is_name)
    if disp: display(Markdown(f'[{func_name}]({link})'))
    else: return link

def type_repr(t):
    "Representation of type `t` (in a type annotation)"
    if getattr(t, '__args__', None):
        args = t.__args__
        if len(args)==2 and args[1] == type(None):
            return f'`Optional`\[{type_repr(args[0])}\]'
        reprs = ', '.join([type_repr(o) for o in args])
        return f'{doc_link(get_name(t))}\[{reprs}\]'
    else: return doc_link(get_name(t))

_arg_prefixes = {inspect._VAR_POSITIONAL: '\*', inspect._VAR_KEYWORD:'\*\*'}

def format_param(p):
    "Formats function param to `param1:Type=val`. Font weights: param1=bold, val=italic"
    arg_prefix = _arg_prefixes.get(p.kind, '') # asterisk prefix for *args and **kwargs
    res = f"**{arg_prefix}`{p.name}`**"
    if hasattr(p, 'annotation') and p.annotation != p.empty: res += f':{type_repr(p.annotation)}'
    if p.default != p.empty:
        default = getattr(p.default, 'func', p.default) #For partials
        default = getattr(default, '__name__', default) #Tries to find a name
        if is_enum(default.__class__):                  #Enum have a crappy repr
            res += f'=*`{default.__class__.__name__}.{default.name}`*'
        else: res += f'=*`{repr(default)}`*'
    return res

def _format_enum_doc(enum, full_name):
    "Formatted `enum` definition to show in documentation"
    vals = ', '.join(enum.__members__.keys())
    return f'<code>{full_name}</code>',f'<code>Enum</code> = [{vals}]'

def _escape_chars(s):
    return s.replace('_', '\_')

def _format_func_doc(func, full_name=None):
    "Formatted `func` definition to show in documentation"
    try:
        sig = inspect.signature(func)
        fmt_params = [format_param(param) for name,param
                  in sig.parameters.items() if name not in ('self','cls')]
    except: fmt_params = []
    name = f'<code>{full_name or func.__name__}</code>'
    arg_str = f"({', '.join(fmt_params)})"
    f_name = f"<code>class</code> {name}" if inspect.isclass(func) else name
    return f'{f_name}',f'{name}{arg_str}'

def _format_cls_doc(cls, full_name):
    "Formatted `cls` definition to show in documentation"
    parent_class = inspect.getclasstree([cls])[-1][0][1][0]
    name,args = _format_func_doc(cls, full_name)
    if parent_class != object: args += f' :: {doc_link(get_name(parent_class))}'
    return name,args

def show_doc(elt, doc_string=True, name=None, title_level=None, disp=True, default_cls_level=2):
    "Show documentation for element `elt`. Supported types: class, function, and enum."
    elt = getattr(elt, '__func__', elt)
    name = name or qual_name(elt)
    if inspect.isclass(elt):
        if is_enum(elt.__class__):   name,args = _format_enum_doc(elt, name)
        else:                        name,args = _format_cls_doc (elt, name)
    elif isinstance(elt, Callable):  name,args = _format_func_doc(elt, name)
    else:                            name,args = f"<code>{name}</code>", ''
    link = get_source_link(elt)
    source_link = f'<a href="{link}" class="source_link" style="float:right">[source]</a>'
    title_level = title_level or (default_cls_level if inspect.isclass(elt) else 4)
    doc =  f'<h{title_level} id="{name}" class="doc_header">{name}{source_link}</h{title_level}>'
    doc += f'\n\n> {args}\n\n' if len(args) > 0 else '\n\n'
    if doc_string and inspect.getdoc(elt): doc += add_doc_links(inspect.getdoc(elt))
    if disp: display(Markdown(doc))
    else: return doc

def md2html(md):
    "Convert markdown `md` to HTML code"
    if nbconvert.__version__ < '5.5.0': return HTMLExporter().markdown2html(md)
    else: return HTMLExporter().markdown2html(defaultdict(lambda: defaultdict(dict)), md)

def doc(elt):
    "Show `show_doc` info in preview window"
    md = show_doc(elt, disp=False)
    output = md2html(md)
    if IN_COLAB: get_ipython().run_cell_magic(u'html', u'', output)
    else:
        try: page.page({'text/html': output})
        except: display(Markdown(md))