# MKDocs-Autodoc

Auto generate API document in MKDocs, just like autodoc for Sphinx.

## Install

    pip install git+https://github.com/restaction/mkdocs-autodoc.git
    
After install this plugin, it will auto patch mkdocs and disable --theme option
of mkdocs cli in order to use custom theme in ReadTheDocs.

See issues below if you wonder **Why should I patch**:  
https://github.com/rtfd/readthedocs.org/issues/978  
https://github.com/mkdocs/mkdocs/issues/206  

## Usage

Write a *.autodoc file, which contains which should be rendered in your page.

The syntax is:

    module
    package.module
    module::ClassName
    package.module::ClassName

Each line contains a module or class, use `::` to split module and class. 
This plugin will render functions which defined in the module you selected, 
or methods of the class you selected, built-in, private, speciall
functions/methods will be ignored.

This plugin works well for
[Google](https://google.github.io/styleguide/pyguide.html#Comments) style docstrings, 
it not works well for [NumPy](https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt) and [Sphinx](http://www.sphinx-doc.org/en/stable/ext/autodoc.html) style docstrings currently.

Then add the *.autodoc file(eg: api.autodoc) to mkdocs.yml:

    site_name: AutodocDemo
    pages:
      - Home: index.md
      - API: api.autodoc

Save and restart `mkdocs serve`, it will works.

## Who use it

[Flask-Restaction简体中文文档](https://github.com/restaction/docs-zh_CN)  
[Flask-Restaction English document](https://github.com/restaction/docs-en)  
