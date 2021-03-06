from setuptools import setup

setup(
    name="mkdocs-autodoc",
    version="0.1.2",
    url="https://github.com/restaction/mkdocs-autodoc",
    license="MIT",
    description="Auto generate API document in MKDocs",
    author="guyskk",
    author_email="guyskk@qq.com",
    keywords=["mkdocs"],
    packages=["mkdocs_autodoc"],
    py_modules=["magicpatch"],
    package_data={
        "mkdocs_autodoc": ["autodoc.jinja2"]
    },
    include_package_data=True,
    entry_points={
        "mkdocs.themes": [
            "autodoc = mkdocs_autodoc",
        ]
    },
    zip_safe=False
)
