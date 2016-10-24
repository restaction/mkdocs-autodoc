"""
MKDocs-Autodoc

This plugin implemented autodoc in MKDocs, just like autodoc in Sphinx.
Doc strings should follow Google Python Style, otherwise will not well parsed.
"""
import io
import os
from mkdocs import utils
from mkdocs.config import load_config
from mkdocs.commands import build
from mkdocs.commands.build import log, get_global_context, get_page_context
from mkdocs.toc import TableOfContents, AnchorLink
from mkdocs_autodoc.autodoc import parse_selected
from magicpatch import patch

AUTODOC_MARK = ".autodoc"
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "autodoc.jinja2")

# hack
import pip
from pprint import pprint
pprint(sorted([
    "%s==%s" % (i.key, i.version)
    for i in pip.get_installed_distributions()
]))


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


def get_complete_paths(config, page):
    """
    Return the complete input/output paths for the supplied page.
    """
    input_path = os.path.join(config['docs_dir'], page.input_path)
    output_path = os.path.join(config['site_dir'], page.output_path)
    return input_path, output_path


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
    contents, titles = parse_selected(input_content)
    table_of_contents = create_toc(titles)
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


@patch(build._build_page)
def build_page(f, page, *args, **kwargs):
    """
    A patch of mkdocs.commands.build._build_page
    """
    if page.input_path.endswith(AUTODOC_MARK):
        return build_autodoc(page, *args, **kwargs)
    return f(page, *args, **kwargs)


@patch(build.build)
def patched_build(f, config, *args, **kwargs):
    print("HACK".center(60, "-"))
    real_config = load_config(config_file=None)
    for k in ["theme", "theme_dir"]:
        config[k] = real_config[k]
    return f(config, *args, **kwargs)


# ---------------------------------------------------------------------
#                               Demo                                  |
# ---------------------------------------------------------------------


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
