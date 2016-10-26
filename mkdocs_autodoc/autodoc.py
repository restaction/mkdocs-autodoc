"""
Autodoc

Some useful functions for parsing doc string of modules.
"""
import importlib
import inspect
import pydoc
from markdown import markdown

EXTENSIONS = ['nl2br', 'tables', 'fenced_code']
DOC_STRING_MARKS = ["Args", "Returns", "Yields", "Raises", "Attributes"]


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
        parsed[mark] = markdown(
            inspect.cleandoc(content), extensions=EXTENSIONS)
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
    desc = markdown(desc, extensions=EXTENSIONS)
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
        if hasattr(obj, "__init__"):
            signature = str(inspect.signature(obj.__init__))
            return "class %s%s" % (name, signature)
        else:
            signature = "%s()" % name
    elif inspect.ismodule(obj):
        signature = name
    else:
        signature = str(inspect.signature(obj))
        return name + signature
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
        # exclude not routines
        if not inspect.isroutine(x):
            return False
        # exclude private and special
        if x.__name__.startswith("_"):
            return False
        # exclude routines not defined in the module
        if inspect.ismodule(obj) and inspect.getmodule(x) != obj:
            return False
        return True
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


def get_name(obj):
    """
    Get the name of object
    """
    if inspect.isclass(obj):
        name = pydoc.classname(obj, None)
    name = obj.__name__
    return name.rsplit(".", maxsplit=1)[-1]


def parse_selected(text):
    """
    Parse selected module and class

    Returns:
        tuple(contents, titles)
    """
    titles = []
    contents = []
    for obj in load_selected(text):
        titles.append(get_name(obj))
        item = parse_module_or_class(obj)
        contents.append(item)
    return contents, titles
