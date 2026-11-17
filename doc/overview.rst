Overview
========

scim2-cli sends the requests of the **System for Cross-domain Identity Management** (**SCIM**)
protocol from the command line. It discovers the resource types and the schemas of the server,
and checks the payloads it sends and receives with
`scim2-models <https://scim2-models.readthedocs.io>`_.

This page introduces the commands, from the connection to the server to the compliance check.
It assumes that scim2-cli is :doc:`installed <installation>` and that a SCIM server is available.
The :doc:`how-to guides <how-to/index>` cover focused tasks,
and the :doc:`reference` lists every command and option.

.. tip::

   `scim2-server <https://scim2-server.readthedocs.io>`__ runs a SCIM server to try the commands:

   .. code-block:: console

        $ pip install scim2-server
        $ scim2-server

   The server answers on http://127.0.0.1:8080.

Connect to a server
-------------------

Pass the URL of the server with :option:`--url <scim2 --url>`.
Pass additional headers, such as authentication ones, with :option:`--header <scim2 --header>`.

.. code-block:: console

    $ scim2 --url https://auth.example --header "Authorization: Bearer 12345" create user --user-name "bjensen@example.com"
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "2819c223-7f76-453a-919d-413861904646",
        "userName": "bjensen@example.com",
        "meta": {
            "resourceType": "User",
            "created": "2010-01-23T04:56:22Z",
            "lastModified": "2011-05-13T04:42:34Z",
            "version": "W/\"3694e05e9dff590\"",
            "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646"
        }
    }

To set them once for all the commands, use the :ref:`SCIM_CLI_URL <scim2-url-scim_cli_url>`
and :ref:`SCIM_CLI_HEADERS <scim2-header-scim_cli_headers>` environment variables.

.. code-block:: console

    $ export SCIM_CLI_URL="https://auth.example"
    $ export SCIM_CLI_HEADERS="Authorization: Bearer 12345"
    $ scim2 create user --user-name "bjensen@example.com"

.. warning::

   Other users of the machine can see the command line arguments, for instance with ``ps``.
   The shell history also keeps them.
   Pass secrets such as authentication tokens with :ref:`SCIM_CLI_HEADERS <scim2-header-scim_cli_headers>` instead of :option:`--header <scim2 --header>`.
   Read them from a file rather than typing them:

   .. code-block:: console

       $ export SCIM_CLI_HEADERS="Authorization: Bearer $(cat ~/.scim-token)"

Before sending a request, scim2-cli queries the discovery endpoints of the server.
:doc:`how-to/skip-the-discovery` saves these requests.

Query and search resources
--------------------------

Use the :ref:`reference:query` and :ref:`reference:search` commands to look for resources.
:ref:`reference:query` performs a ``GET`` request on the resources endpoint, while :ref:`reference:search` performs a ``POST`` request on the ``/.search`` endpoint.
Both commands take similar options such as :option:`--count <scim2-query --count>` or :option:`--attribute <scim2-query --attribute>`.
:ref:`reference:query` also takes a :option:`RESOURCE_TYPE <scim2-query RESOURCE_TYPE>` and an :option:`ID <scim2-query ID>` argument.
:option:`RESOURCE_TYPE <scim2-query RESOURCE_TYPE>` is the name of a resource type of the server, in any case, such as ``user`` or ``group``.
:ref:`reference:search` takes an optional :option:`RESOURCE_TYPE <scim2-search RESOURCE_TYPE>` too.

- Without arguments, the command queries all the resources of the server.

  .. code-block:: console
      :caption: Querying all the resources from the server.

      $ scim2 query
      {
          "schemas": [
              "urn:ietf:params:scim:api:messages:2.0:ListResponse"
          ],
          "totalResults": xx,
          "startIndex": 1,
          "itemsPerPage": 50,
          "Resources": [...]
      }

- With :option:`RESOURCE_TYPE <scim2-query RESOURCE_TYPE>` alone, the command queries all the resources of this type.

  .. code-block:: console
      :caption: Querying all the users from the server.

      $ scim2 query user
      {
          "schemas": [
              "urn:ietf:params:scim:api:messages:2.0:ListResponse"
          ],
          "totalResults": xx,
          "startIndex": 1,
          "itemsPerPage": 50,
          "Resources": [...]
      }

- With both arguments, the command queries the resource with this ID.

  .. code-block:: console
      :caption: Querying the user with the ID `38b044dd95624c4186f5614fca30305d`

      $ scim2 query user 38b044dd95624c4186f5614fca30305d
      {
          "schemas": [
              "urn:ietf:params:scim:schemas:core:2.0:User",
              "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
          ],
          "id": "38b044dd95624c4186f5614fca30305d",
          "meta": {
              "resourceType": "User",
              "created": "2024-12-05T16:08:51.896646Z",
              "lastModified": "2024-12-05T16:08:51.896646Z",
              "location": "http://scim.example/v2/Users/38b044dd95624c4186f5614fca30305d",
              "version": "W/\"637b1ce03c010cd55fe45b6f7be2247b5159b135\""
          },
          "userName": "bjensen@example.com"
      }

Create and replace resources
----------------------------

Use the :ref:`reference:create` and :ref:`reference:replace` commands to edit resources.

The options of these commands follow the attributes of the resources on the server.
For instance, the :class:`~scim2_models.User` resource gives a ``--user-name`` option.
``scim2 create user --help`` lists the options.

.. code-block:: console
   :caption: Creation of a user.

   $ scim2 create user --user-name bjensen@example.com
   {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
        ],
        "id": "38b044dd95624c4186f5614fca30305d",
        "meta": {
            "resourceType": "User",
            "created": "2024-12-05T16:08:51.896646Z",
            "lastModified": "2024-12-05T16:08:51.896646Z",
            "location": "http://scim.example/v2/Users/38b044dd95624c4186f5614fca30305d",
            "version": "W/\"637b1ce03c010cd55fe45b6f7be2247b5159b135\""
        },
        "userName": "bjensen@example.com"
    }

Modify resources
----------------

The :ref:`reference:modify` command sends patch operations to a resource.
The operations follow the resource type and the id, and are applied in order:
``add PATH VALUE``, ``replace PATH VALUE`` and ``remove PATH``.
Values of string attributes are passed as is, the other values are passed in JSON.

.. code-block:: console
   :caption: Modification of a user.

   $ scim2 modify user 38b044dd95624c4186f5614fca30305d \
       replace displayName "Barbara Jensen" \
       replace active false \
       add emails '[{"value": "bjensen@example.com", "type": "work"}]'

The server answers with the modified resource, or without content.

Delete resources
----------------

The :ref:`reference:delete` command deletes a resource.

.. code-block:: console
   :caption: Deletion of a user.

   $ scim2 delete user 38b044dd95624c4186f5614fca30305d

Act on the authenticated client
-------------------------------

Pass :option:`--me <scim2-query --me>` to :ref:`reference:query`, :ref:`reference:create`, :ref:`reference:replace`, :ref:`reference:modify` or :ref:`reference:delete`
to act on the resource of the authenticated client, under ``/Me``.
The server answers with a ``501`` error if it does not support ``/Me``.

.. code-block:: console
   :caption: Reading the resource of the authenticated client.

   $ scim2 query --me

:ref:`reference:replace` needs no ``--id`` with ``--me``:

.. code-block:: console
   :caption: Replacing the resource of the authenticated client.

   $ scim2 replace user --me --user-name bjensen@example.com

Send a JSON payload
-------------------

scim2-cli reads a JSON payload on the standard input.
Use it to send custom payloads to the SCIM server.

With :ref:`reference:query` and :ref:`reference:search`, the payload is a :class:`~scim2_models.SearchRequest` object:

.. code-block:: console
   :caption: Search of a user by passing a custom payload.

   $ echo '{"startIndex": 50, "count": 10}' | scim2 query user
   {
        "schemas": [
            "urn:ietf:params:scim:api:messages:2.0:ListResponse"
        ],
        "totalResults": xx,
        "startIndex": 50,
        "itemsPerPage": 10,
        "Resources": [...]
    }

With :ref:`reference:create` and :ref:`reference:replace`, the command needs no resource type: the endpoint comes from the ``schemas`` of the payload.

.. code-block:: console
   :caption: Creation of a user by passing a custom payload.

   $ echo '{"userName": "bjensen@example.com", "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]}' | scim2 create
   {
        "schemas": [
            "urn:ietf:params:scim:schemas:core:2.0:User",
            "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
        ],
        "id": "38b044dd95624c4186f5614fca30305d",
        "meta": {
            "resourceType": "User",
            "created": "2024-12-05T16:08:51.896646Z",
            "lastModified": "2024-12-05T16:08:51.896646Z",
            "location": "http://scim.example/v2/Users/38b044dd95624c4186f5614fca30305d",
            "version": "W/\"637b1ce03c010cd55fe45b6f7be2247b5159b135\""
        },
        "userName": "bjensen@example.com"
    }

With :ref:`reference:bulk`, the payload is a :class:`~scim2_models.BulkRequest` object.
The command checks the request against the bulk capabilities of the server before sending it.

.. code-block:: console
   :caption: Creation of a user in a bulk request.

   $ echo '{"schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkRequest"], "Operations": [{"method": "POST", "path": "/Users", "bulkId": "qwerty", "data": {"schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"], "userName": "bjensen@example.com"}}]}' | scim2 bulk
   {
       "schemas": [
           "urn:ietf:params:scim:api:messages:2.0:BulkResponse"
       ],
       "Operations": [
           {
               "method": "POST",
               "bulkId": "qwerty",
               "location": "http://scim.example/v2/Users/92b725cd9465",
               "status": "201"
           }
       ]
   }

Read the errors
---------------

When the server answers an error, the command displays it on stdout and fails with the exit code 1.
A summary of the error goes to stderr, so another program can still read the output.

.. code-block:: console
   :caption: Querying a user that does not exist.

   $ scim2 query user unknown-id
   {
       "schemas": [
           "urn:ietf:params:scim:api:messages:2.0:Error"
       ],
       "status": "404",
       "detail": "Resource unknown-id not found"
   }
   Error: 404 Resource unknown-id not found
   $ echo $?
   1

The :ref:`reference:bulk` command fails the same way when some operations of the bulk response failed.

Check the compliance of a server
--------------------------------

The :ref:`reference:test` command creates, edits and deletes resources to check that the server
complies with the SCIM specifications, with
:doc:`scim2-tester <scim2_tester:index>`.

.. code-block:: console

    $ scim2 test
    Performing a SCIM compliance check on http://localhost:8080 ...
    300 passed (seed 2416347125)

:doc:`how-to/check-the-compliance-of-a-server` shows how to read the results, replay a run and select the checks.
