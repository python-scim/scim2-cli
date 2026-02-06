Tutorial
========

The :ref:`cli` command allows you to interact with a SCIM server.

.. tip::

   If you want to test scim2-cli with a real SCIM server, you can install and run `scim2-server <https://github.com/python-scim/scim2-server>`__:

   .. code-block:: shell

        $ pip install scim2-server
        $ scim2-server

   Then you have a functional SCIM server available at http://127.0.0.1:8080 that you can use to test the different commands.

Basic parameters
----------------

In order to connect to a SCIM server you will need to pass the :option:`--url <scim --url>` parameter.
You can also pass additional headers, such as authentication ones, with :option:`--header <scim --header>`.

.. code-block:: shell

    $ scim2 --url https://auth.example --header "Authorization: Bearer 12345" create user --user-name "bjensen@example.com"
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "2819c223-7f76-453a-919d-413861904646",
        "userName": "bjensen@example.com",
        "meta": {
            "resourceType": "User",
            "created": "2010-01-23T04:56:22Z",
            "lastModified": "2011-05-13T04:42:34Z",
            "version": 'W\\/"3694e05e9dff590"',
            "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
        },
    }

However passing those parameters each time you use the command can be annoying.
To make commands shorter, you can set those parameters once for all by using the :ref:`SCIM_CLI_URL <scim-url-scim_cli_url>` and :ref:`SCIM_CLI_HEADERS <scim-header-scim_cli_headers>` environment vars.

.. code-block:: shell

    $ export SCIM_CLI_URL="https://auth.example"
    $ export SCIM_CLI_HEADERS="Authorization: Bearer 12345"
    $ scim2 create user --user-name "bjensen@example.com"
    {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": "2819c223-7f76-453a-919d-413861904646",
        "userName": "bjensen@example.com",
        "meta": {
            "resourceType": "User",
            "created": "2010-01-23T04:56:22Z",
            "lastModified": "2011-05-13T04:42:34Z",
            "version": 'W\\/"3694e05e9dff590"',
            "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
        },
    }


Server configuration
--------------------

Before doing anything, the CLI needs to reach the server configuration to find out which features are available,
which resource schemas are available, and where they are located.

By default the CLI will automatically discover those resources on the server, before each command is run.

However, automatic discovery can be slow due to multiple network requests.
You can store those data locally and reuse them for future command runs thanks to the
:option:`--schemas <scim --schemas>`, :option:`--resource-types <scim --resource-types>` and :option:`--service-provider-config <scim --service-provider-config>` (and their corresponding environment vars :ref:`SCIM_CLI_SCHEMAS <scim-schemas-scim_cli_schemas>`, :ref:`SCIM_CLI_RESOURCE_TYPES <scim-resource_types-scim_cli_resource_types>` and :ref:`SCIM_CLI_SERVICE_PROVIDER_CONFIG <scim-service_provider_config-scim_cli_service_provider_config>`)

.. code-block:: shell
    :caption: Save the configuration resources

    $ scim query schema > /tmp/schemas.json
    $ scim query resourcetype > /tmp/resource-types.json
    $ scim query serviceproviderconfig > /tmp/service-provider-config.json

.. code-block:: shell
    :caption: Load the cached resources

    $ export SCIM_SCHEMAS=/tmp/schemas.json
    $ export SCIM_RESOURCE_TYPES=/tmp/resource-types.json
    $ export SCIM_SERVICE_PROVIDER_CONFIG=/tmp/service-provider-config.json
    $ scim2 query ...

Query and search resources
--------------------------

Use the :ref:`query` and :ref:`search` commands to look for resources.
:ref:`query` performs a `GET` request on the resources endpoint, while :ref:`search` performs a `POST` request on the ``/.search`` endpoint.
Both commands take similar options such as :option:`--count <scim-query.--count>` or :option:`--attributes <scim-query.--attributes>`.
An exhaustive list of options can be found on the :doc:`reference`.
:ref:`query` can also take a :option:`RESOURCE_TYPE <scim-query.RESOURCE_TYPE>` and a :option:`ID <scim-query.ID>` parameters.

- If none are set, all the resources of the server are queried.

  .. code-block:: console
      :caption: Querying all the resources from the server.

      $ scim query
      {
          "schemas": [
              "urn:ietf:params:scim:api:messages:2.0:ListResponse"
          ],
          "totalResults": xx,
          "startIndex": 1,
          "itemsPerPage": 50,
          "Resources": [...]
      }
- If :option:`RESOURCE_TYPE <scim-query.RESOURCE_TYPE>` is set and :option:`ID <scim-query.ID>` is unset, all the resource of the kind passed in parameter are returned.

  .. code-block:: console
      :caption: Querying all the users from the server.

      $ scim query user
      {
          "schemas": [
              "urn:ietf:params:scim:api:messages:2.0:ListResponse"
          ],
          "totalResults": xx,
          "startIndex": 1,
          "itemsPerPage": 50,
          "Resources": [...]
      }

- If both options are set, the very resource with the ID are returned.

  .. code-block:: console
      :caption: Querying the user with the ID `38b044dd95624c4186f5614fca30305d`

      $ scim query user 38b044dd95624c4186f5614fca30305d
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

Use the :ref:`create` and :ref:`replace` commands to edit resources.

Options for those commands are dynamically generated, depending on the resource attributes available on the server.
For instance, for the :class:`~scim2_models.User` resource, you have a ``--user-name`` option.
You can have a look at the exhaustive list of options by running ``scim create user --help``.

.. code-block:: console
   :caption: Creation of an user.

   $ scim create user --user-name bjensen@example.com
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

Delete resources
----------------

The :ref:`delete` command allows you to delete resources.

.. code-block:: console
   :caption: Deletion of an user.

   $ scim delete user 38b044dd95624c4186f5614fca30305d

Perform a SCIM compliance test
------------------------------

The :ref:`test` command runs a series of resource creation, edition and deletions to check that your server complies with the SCIM specifications.
See the :doc:`scim2-tester documentation <scim2_tester:index>` for more details on which tests are performed.

.. code-block:: console
   :caption: SCIM compliance test

    $ scim test
    Performing a SCIM compliance check on http://localhost:8080 ...
    SUCCESS check_service_provider_config_endpoint
    SUCCESS check_query_all_resource_types
    SUCCESS check_query_resource_type_by_id
      Successfully accessed the /ResourceTypes/User endpoint.
    SUCCESS check_query_resource_type_by_id
      Successfully accessed the /ResourceTypes/Group endpoint.
    SUCCESS check_access_invalid_resource_typ
    ...

JSON input
----------

scim2-cli will also read input data from the standard input.
Use this to send custom payloads to the SCIM server.

When user with :ref:`query` and :ref:`search`, the input value must be a JSON representation of a :class:`~scim2_models.SearchRequest` object:

.. code-block:: console
   :caption: Search of an user by passing a custom payload.

   $ echo '{"startIndex": 50, "count": 10}' | scim query user
   {
        "schemas": [
            "urn:ietf:params:scim:api:messages:2.0:ListResponse"
        ],
        "totalResults": xx,
        "startIndex": 50,
        "itemsPerPage": 10,
        "Resources": [...]
    }

When used with :ref:`create` and :ref:`replace`, no subcommand is needed and the endpoint is guessed from the payload.

.. code-block:: console
   :caption: Creation of an user by passing a custom payload.

   $ echo '{"userName": "bjensen@example.com", "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]}' | scim create
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
