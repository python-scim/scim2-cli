import datetime
import os
import sys
from importlib import metadata

from docutils import nodes
from sphinx_iconify.roles import depart_iconify_icon_html
from sphinx_iconify.roles import iconify_icon
from sphinx_iconify.roles import visit_iconify_icon_html

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
nitpicky = True
autosectionlabel_prefix_document = True
suppress_warnings = ["autosectionlabel.changelog"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "scim2_models": ("https://scim2-models.readthedocs.io/en/latest/", None),
    "scim2_client": ("https://scim2-client.readthedocs.io/en/latest/", None),
    "scim2_tester": ("https://scim2-tester.readthedocs.io/en/latest/", None),
}

# -- Sibling projects ------------------------------------------------------

# Kept identical in every python-scim documentation, so that any divergence
# shows up in a diff.
NAV_LINKS = [
    {
        "title": "Libraries",
        "children": [
            {
                "title": "scim2-models",
                "url": "https://scim2-models.readthedocs.io",
                "summary": "SCIM resources and messages as Pydantic models",
            },
            {
                "title": "scim2-client",
                "url": "https://scim2-client.readthedocs.io",
                "summary": "Pythonically build SCIM requests and parse SCIM responses",
            },
        ],
    },
    {
        "title": "Tools",
        "children": [
            {
                "title": "scim2-tester",
                "url": "https://scim2-tester.readthedocs.io",
                "summary": "Check a SCIM server for RFC compliance",
            },
            {
                "title": "scim2-cli",
                "url": "https://scim2-cli.readthedocs.io",
                "summary": "Query a SCIM server from the command line",
            },
            {
                "title": "scim2-server",
                "url": "https://github.com/python-scim/scim2-server",
                "summary": "A lightweight SCIM2 server prototype",
            },
            {
                "title": "pytest-scim2-server",
                "url": "https://github.com/pytest-dev/pytest-scim2-server",
                "summary": "A SCIM2 server fixture for pytest",
            },
        ],
    },
    {
        "title": "Integrations",
        "children": [
            {
                "title": "scim2-flask",
                "url": "https://scim2-flask.readthedocs.io",
                "summary": "Painless SCIM integration for Flask",
            },
            {
                "title": "scim2-django",
                "url": "https://scim2-django.readthedocs.io",
                "summary": "Painless SCIM integration for Django",
            },
            {
                "title": "scim2-fastapi",
                "url": "https://scim2-fastapi.readthedocs.io",
                "summary": "Painless SCIM integration for FastAPI",
            },
        ],
    },
]

# -- Options for HTML output ----------------------------------------------

html_theme = "shibuya"
# html_static_path = ["_static"]
html_baseurl = "https://scim2-cli.readthedocs.io"
html_logo = "_static/python-scim.svg"
html_theme_options = {
    "globaltoc_expand_depth": 3,
    "accent_color": "orange",
    "github_url": "https://github.com/python-scim/scim2-cli",
    "mastodon_url": "https://toot.aquilenet.fr/@yaal",
    "nav_links": NAV_LINKS,
}
html_context = {
    "source_type": "github",
    "source_user": "python-scim",
    "source_repo": "scim2-cli",
    "source_version": "main",
    "source_docs_path": "/doc/",
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


def _visit_iconify_skip(self, node):
    raise nodes.SkipNode


def setup(app):
    app.add_node(
        iconify_icon,
        override=True,
        html=(visit_iconify_icon_html, depart_iconify_icon_html),
        man=(_visit_iconify_skip, None),
    )
