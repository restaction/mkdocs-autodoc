from setuptools import setup

setup(
    name="mkdocs-autodoc",
    version="0.1.0",
    url="https://github.com/restaction/mkdocs-autodoc",
    license="MIT",
    description="Auto generate API document in MKDocs",
    author="guyskk",
    author_email="guyskk@qq.com",
    keywords=["mkdocs"],
    py_module=["mkdocs_autodoc.py"],
    include_package_data=True,
    entry_points={
        "mkdocs.themes": [
            "autodoc = mkdocs_autodoc",
        ]
    },
    zip_safe=False
)
