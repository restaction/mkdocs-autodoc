import io
import os
import importlib
import inspect
import pydoc
import markdown
from mkdocs import utils
from mkdocs.commands import build
from mkdocs.commands.build import log, get_global_context, get_page_context
from mkdocs.toc import TableOfContents, AnchorLink
_build_page = build._build_page

AUTODOC_MARK = ".autodoc"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "autodoc.jinja2")


class DocError(Exception):
    """Doc string not satisfied with Google Python Style"""


def get_complete_paths(config, page):
    """
    Return the complete input/output paths for the supplied page.
    """
    input_path = os.path.join(config['docs_dir'], page.input_path)
    output_path = os.path.join(config['site_dir'], page.output_path)
    return input_path, output_path


def load_selecting(text):
    result = []
    for line in text.splitlines():
        if not line:
            continue
        if "::" in line:
            module, classname = line.rsplit("::", maxsplit=1)
            module = importlib.import_module(module)
            result.append(getattr(module, classname))
        else:
            result.append(importlib.import_module(line))
    return result

DOC_STRING_MARKS = ["Args", "Returns", "Yields", "Raises", "Attributes"]


def parse_meta(meta):
    """
    Parse DOC_STRING_MARKS
    """
    parsed = {}
    for section in meta:
        mark, content = section.split("\n", maxsplit=1)
        mark = mark.strip("\n:")
        parsed[mark] = markdown.markdown(inspect.cleandoc(content))
    return parsed


def split_doc(doc):
    """
    Split docstring into desc and meta

    Returns:
        A tuple of desc, meta.

        desc: the description part
        meta: a list of sections of the meta part
    """
    indexs = []
    for mark in DOC_STRING_MARKS:
        i = doc.find("%s:" % mark)
        if i >= 0:
            indexs.append(i)
    if not indexs:
        return doc, []
    indexs = sorted(indexs)
    desc = doc[:indexs[0]]
    sections = []
    for i, j in zip(indexs[:-1], indexs[1:]):
        sections.append(doc[i:j])
    sections.append(doc[indexs[-1]:])
    return desc, sections


def parse_doc(doc):
    if not doc:
        return "", []
    desc, meta = split_doc(doc)
    desc = markdown.markdown(desc)
    meta = parse_meta(meta)
    return desc, meta


def parse_routine(obj):
    signature = pydoc.plaintext.docroutine(obj).split('\n', maxsplit=1)[0]
    desc, meta = parse_doc(inspect.getdoc(obj))
    return {"signature": signature, "desc": desc, "meta": meta}


def parse_module_or_class(obj):
    routines = inspect.getmembers(obj, inspect.isroutine)
    desc, meta = parse_doc(inspect.getdoc(obj))
    parsed = [parse_routine(obj) for name, obj in routines]
    return {"routines": parsed, "desc": desc, "meta": meta}


def parse_selecting(text):
    titles = []
    contents = []
    for obj in load_selecting(text):
        titles.append(obj.__name__)
        item = parse_module_or_class(obj)
        contents.append(item)
    toc = create_toc(titles)
    return contents, toc


def create_toc(titles):
    toc = TableOfContents("")
    if not titles:
        return toc
    first = titles.pop(0)
    link = AnchorLink(title=first, url="#0")
    link.active = True
    link.children = [
        AnchorLink(title=title, url="#%d" % (index + 1))
        for index, title in enumerate(titles)
    ]
    toc.items = [link]
    return toc


def build_autodoc(page, config, site_navigation, env, dump_json, dirty=False):
    input_path, output_path = get_complete_paths(config, page)
    try:
        input_content = io.open(input_path, 'r', encoding='utf-8').read()
    except IOError:
        log.error('file not found: %s', input_path)
        raise
    # render autodoc contents
    tmplstr = io.open(TEMPLATE_PATH).read()
    template = env.from_string(tmplstr)
    contents, table_of_contents = parse_selecting(input_content)
    html_content = template.render(contents=contents)
    # render page
    meta = None
    context = get_global_context(site_navigation, config)
    context.update(get_page_context(
        page, html_content, table_of_contents, meta, config
    ))
    template = env.get_template('base.html')
    output_content = template.render(context)
    utils.write_file(output_content.encode('utf-8'), output_path)
    return html_content, table_of_contents, None


def build_page(page, *args, **kwargs):

    if page.input_path.endswith(AUTODOC_MARK):
        return build_autodoc(page, *args, **kwargs)
    return _build_page(page, *args, **kwargs)


build._build_page = build_page
