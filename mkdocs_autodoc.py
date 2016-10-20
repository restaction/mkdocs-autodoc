"""
MKDocs-Autodoc

This plugin implemented autodoc in MKDocs, just like autodoc in Sphinx.
Doc strings should follow Google Python Style, otherwise will not well parsed.
"""
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
DOC_STRING_MARKS = ["Args", "Returns", "Yields", "Raises", "Attributes"]


def get_complete_paths(config, page):
    """
    Return the complete input/output paths for the supplied page.
    """
    input_path = os.path.join(config['docs_dir'], page.input_path)
    output_path = os.path.join(config['site_dir'], page.output_path)
    return input_path, output_path


def load_selected(text):
    """
    Load selected module or class in text

    text syntax:

        module
        package.module
        module::class

    Returns:
        A list of loaded objects
    """
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


def parse_meta(meta):
    """
    Parse returns meta of split_doc

    Returns:
        A dict of parsed meta
    """
    parsed = {}
    for section in meta:
        mark, content = section.split("\n", maxsplit=1)
        mark = mark.strip("\n:")
        parsed[mark] = markdown.markdown(inspect.cleandoc(content))
    return parsed


def split_doc(doc):
    """
    Split docstring into title, desc and meta

    Returns:
        A tuple of title, desc, meta.

        title: the summary line of doc
        desc: the description part
        meta: a list of sections of the meta part
    """
    if not doc:
        return "", "", []
    # split title/desc,meta
    lines = doc.strip().split("\n", maxsplit=1)
    if len(lines) == 1:
        return lines[0], "", []
    title, doc = lines
    # split desc/meta
    indexs = []
    for mark in DOC_STRING_MARKS:
        i = doc.find("%s:" % mark)
        if i >= 0:
            indexs.append(i)
    if not indexs:
        return title, doc, []
    indexs = sorted(indexs)
    desc = doc[:indexs[0]]
    # split meta into sections
    sections = []
    for i, j in zip(indexs[:-1], indexs[1:]):
        sections.append(doc[i:j])
    sections.append(doc[indexs[-1]:])
    return title, desc, sections


def parse_doc(doc):
    """
    Parse docstring

    Returns:
        A tuple of title, desc, meta.
    """
    title, desc, meta = split_doc(doc)
    desc = markdown.markdown(desc)
    meta = parse_meta(meta)
    return title, desc, meta


def get_signature(obj):
    """
    Get signature of module/class/routine

    Returns:
        A string signature
    """
    name = obj.__name__
    if inspect.isclass(obj):
        name = pydoc.classname(obj, None)
        init = getattr(obj, '__init__')
        if init:
            signature = pydoc.plaintext\
                .docroutine(init).split('\n', maxsplit=1)[0]
            signature = signature[len("__init__(self, "):-1]
            signature = "class %s(%s)" % (name, signature)
        else:
            signature = "%s()" % name
    elif inspect.ismodule(obj):
        signature = name
    else:
        signature = pydoc.plaintext\
            .docroutine(obj).split('\n', maxsplit=1)[0]
        if inspect.ismethod(obj):
            signature = signature.replace("(self, ", "(")
    return signature


def parse_routine(obj):
    """
    Parse routine object

    Returns:
        A dict, eg:

            {
                "signature": "func(*args, **kwargs)",
                "title": "title",
                "desc": "desc",
                "meta": meta
            }
    """
    title, desc, meta = parse_doc(inspect.getdoc(obj))
    return {
        "signature": get_signature(obj),
        "title": title,
        "desc": desc,
        "meta": meta
    }


def parse_module_or_class(obj):
    """
    Parse module or class and routines in it.

    Returns:
        A dics, eg:

            {
                "routines": routines,
                "signature": signature,
                "title": title,
                "desc": desc,
                "meta": meta
            }
    """
    def predicate(x):
        if inspect.isroutine(x):
            if x.__name__.startswith("_"):
                return False
            return True
        return False
    routines = inspect.getmembers(obj, predicate)
    title, desc, meta = parse_doc(inspect.getdoc(obj))
    parsed = [parse_routine(obj) for name, obj in routines]
    return {
        "routines": parsed,
        "signature": get_signature(obj),
        "title": title,
        "desc": desc,
        "meta": meta
    }


def parse_selected(text):
    """
    Parse selected module and class

    Returns:
        tuple(contents, toc)
    """
    titles = []
    contents = []
    for obj in load_selected(text):
        titles.append(obj.__name__)
        item = parse_module_or_class(obj)
        contents.append(item)
    toc = create_toc(titles)
    return contents, toc


def create_toc(titles):
    """
    Create table of contents
    """
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
    """
    Build autodoc, just like mkdocs.commands.build._build_page
    """
    input_path, output_path = get_complete_paths(config, page)
    try:
        input_content = io.open(input_path, 'r', encoding='utf-8').read()
    except IOError:
        log.error('file not found: %s', input_path)
        raise
    # render autodoc contents
    tmplstr = io.open(TEMPLATE_PATH).read()
    template = env.from_string(tmplstr)
    contents, table_of_contents = parse_selected(input_content)
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
    """
    A patch of mkdocs.commands.build._build_page
    """
    if page.input_path.endswith(AUTODOC_MARK):
        return build_autodoc(page, *args, **kwargs)
    return _build_page(page, *args, **kwargs)


build._build_page = build_page


class Demo:
    """
    A demo of mkdocs-autodoc

    Long description description description description description
    description description description description description description
    description description description description description description

    Usage:

        demo = Demo(title="demo")
        demo.set("hello world")
        print(demo.get)

    Attributes:
        title: demo title

        eg:

            title = "demo"
    Args:
        hahaha
        hahah
    """

    def __init__(self, title):
        """
        Init demo

        Args:
            title: demo title
        """
        self.title = title

    def set(self, title):
        """
        Set demo title

        Args:
            title: demo title
        """
        self.title = title

    def get(self):
        """
        Get demo title

        Returns:
            title: demo title
        """
        return self.title
