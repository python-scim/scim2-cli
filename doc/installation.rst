Installation
============

.. tab-set::

   .. tab-item:: :iconify:`material-icon-theme:uv` uvx.sh
      :sync: uvx-sh

      `uvx.sh <https://uvx.sh>`_ provides an installation script that installs scim2-cli permanently on your system.

      .. tab-set::
         :class: outline

         .. tab-item:: Linux / macOS

            .. code-block:: console

               $ curl -LsSf uvx.sh/scim2-cli/install.sh | sh

         .. tab-item:: Windows

            .. code-block:: powershell

               powershell -ExecutionPolicy ByPass -c "irm https://uvx.sh/scim2-cli/install.ps1 | iex"

      Then you can run:

      .. code-block:: console

         $ scim2 --help

   .. tab-item:: :iconify:`material-icon-theme:uv` uvx
      :sync: uvx

      If you have `uv`__ installed, you can run scim2-cli directly without installing it:

      __ https://docs.astral.sh/uv/

      .. code-block:: console

         $ uvx scim2-cli --help

   .. tab-item:: :iconify:`devicon:pypi` pip
      :sync: pip

      scim2-cli is published on `PyPI <https://pypi.org/project/scim2-cli>`_.

      .. code-block:: console

         $ pip install scim2-cli

      Then you can run:

      .. code-block:: console

         $ scim2 --help

   .. tab-item:: :iconify:`mdi:file-download` Binaries
      :sync: binaries

      Binary files are available on the `releases page <https://github.com/python-scim/scim2-cli/releases>`_.

      .. code-block:: console
         :substitutions:

         $ wget https://github.com/python-scim/scim2-cli/releases/download/|version|/scim2-linux -O scim2
         $ chmod +x scim2
         $ ./scim2 --help

   .. tab-item:: :iconify:`devicon:git` Sources
      :sync: sources

      To run scim2-cli from the sources, `uv`__ is needed:

      __ https://docs.astral.sh/uv/getting-started/installation/

      .. code-block:: console

         $ git clone https://github.com/python-scim/scim2-cli.git
         $ cd scim2-cli
         $ uv sync

      Then you can run it directly:

      .. code-block:: console

         $ uv run scim2 --help

      Or build a single file binary:

      .. code-block:: console

         $ uv sync --group bundle
         $ uv run pyinstaller --name scim2 --onefile scim2_cli/__init__.py
         $ ./dist/scim2 --help
