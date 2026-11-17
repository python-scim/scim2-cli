scim2-cli
=========

scim2-cli sends the requests of the SCIM protocol from the command line,
following :rfc:`RFC7643 <7643>` and :rfc:`RFC7644 <7644>`. It discovers the resource types and
the schemas of the server, gives an option to each attribute, and checks the payloads it sends
and receives with `scim2-models <https://scim2-models.readthedocs.io>`_.
Its ``test`` command checks the compliance of a server with
:doc:`scim2-tester <scim2_tester:index>`.

Install it with:

.. code-block:: console

   $ curl -LsSf uvx.sh/scim2-cli/install.sh | sh

Then send requests to a server:

.. code-block:: console

    $ export SCIM_CLI_URL="https://auth.example/scim/v2"
    $ export SCIM_CLI_HEADERS="Authorization: Bearer $(cat ~/.scim-token)"
    $ scim2 create user --user-name bjensen@example.com
    $ scim2 query user --filter 'userName eq "bjensen@example.com"'
    $ scim2 test

Choose a path
-------------

:doc:`Installation <installation>` lists the other ways to install scim2-cli: pip, uvx, binaries,
a container image or the sources.

:doc:`Overview <overview>` gives a tour of the commands: querying, creating, modifying and deleting
resources, reading the errors and sending JSON payloads.

:doc:`How-to guides <how-to/index>` show how to complete a specific task, such as checking the
compliance of a server in CI.

:doc:`Reference <reference>` lists every command, option and environment variable.

.. toctree::
    :maxdepth: 2
    :hidden:

    Installation <installation>
    Overview <overview>
    How-to guides <how-to/index>
    Reference <reference>
    Contributing <contributing>
    Changelog <changelog>
