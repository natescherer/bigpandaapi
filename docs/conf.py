"""Sphinx configuration."""
project = "The Unofficial BigPanda API Python Library"
author = "Nate Scherer"
copyright = "2023, Nate Scherer"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
