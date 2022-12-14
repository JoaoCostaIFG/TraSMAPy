# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
#import os
#import sys
#
## Location of Sphinx files
#sys.path.insert(0, os.path.abspath(os.path.join("..", "src", "trasmapy")))

project = "TraSMAPy"
copyright = "2022, João de Jesus Costa, Ana Inês Oliveira de Barros, João António Cardoso Vieira e Basto de Sousa"
author = "João de Jesus Costa, Ana Inês Oliveira de Barros, João António Cardoso Vieira e Basto de Sousa"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "autoapi.extension"]

autoapi_type = "python"
autoapi_dirs = ["../src/"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "_templates", "Thumbs.db", ".DS_Store"]

root_doc = "index"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
