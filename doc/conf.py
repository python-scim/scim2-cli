import datetime
import os
import sys
from importlib import metadata

sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../scim2_cli"))

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_click",
    "sphinx_design",
    "sphinx_iconify",
    "sphinx_issues",
    "sphinx_substitution_extensions",
]

templates_path = ["_templates"]
master_doc = "index"
project = "scim2-cli"
year = datetime.datetime.now().strftime("%Y")
copyright = f"{year}, Yaal Coop"
author = "Yaal Coop"
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

version = metadata.version("scim2_cli")
language = "en"

rst_prolog = f"""
.. |version| replace:: {version}
"""

pygments_style = "sphinx"
todo_include_todos = True
toctree_collapse = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "scim2_models": ("https://scim2-models.readthedocs.io/en/latest/", None),
    "scim2_tester": ("https://scim2-tester.readthedocs.io/en/latest/", None),
}

# -- Options for HTML output ----------------------------------------------

html_theme = "shibuya"
# html_static_path = ["_static"]
html_baseurl = "https://scim2-cli.readthedocs.io"
html_theme_options = {
    "globaltoc_expand_depth": 3,
    "accent_color": "orange",
    "github_url": "https://github.com/python-scim/scim2-cli",
    "mastodon_url": "https://toot.aquilenet.fr/@yaal",
    "nav_links": [
        {"title": "scim2-models", "url": "https://scim2-models.readthedocs.io"},
        {
            "title": "scim2-client",
            "url": "https://scim2-client.readthedocs.io",
        },
        {"title": "scim2-tester", "url": "https://scim2-tester.readthedocs.io"},
        {
            "title": "scim2-server",
            "url": "https://github.com/python-scim/scim2-server",
        },
        {
            "title": "pytest-scim2-server",
            "url": "https://github.com/pytest-dev/pytest-scim2-server",
        },
    ],
}

# -- Options for manual page output ---------------------------------------

man_pages = [(master_doc, "scim2-cli", "scim2-cli Documentation", [author], 1)]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        "scim2_cli",
        "scim2_cli Documentation",
        author,
        "scim2_cli",
        "One line description of project.",
        "Miscellaneous",
    )
]

# -- Options for sphinx-issues -------------------------------------

issues_github_path = "python-scim/scim2-cli"
